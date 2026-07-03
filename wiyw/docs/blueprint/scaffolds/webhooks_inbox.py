"""Webhook inbox pattern: verify signature → store raw → 200 fast → process async.

Lift into app/webhooks/. Requires migration 005 (webhooks_inbox).
Shows the full pattern for Brevo; Mailgun/GatewayAPI/Resend reuse receive_webhook()
with their own verifier + dedupe-key extractor (see 08_webhook_design.md).
"""
import hashlib
import hmac
import json
import logging
from typing import Awaitable, Callable, Optional

import asyncpg
from fastapi import APIRouter, BackgroundTasks, Request

from ..config import config
from ..models.db import get_pool
from ..models import repo

log = logging.getLogger("wiyw.inbox")
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

Verifier = Callable[[Request, bytes], Awaitable[Optional[bool]]]  # None = provider unsigned


async def store_inbox(conn: asyncpg.Connection, *, provider: str, event_type: str,
                      dedupe_key: Optional[str], signature_valid: Optional[bool],
                      headers: dict, payload: dict, raw_body: str) -> Optional[str]:
    """Insert the raw webhook. Returns inbox id, or None when it's a duplicate."""
    row = await conn.fetchrow(
        """INSERT INTO webhooks_inbox
             (provider, event_type, dedupe_key, signature_valid, headers, payload, raw_body)
           VALUES ($1,$2,$3,$4,$5::jsonb,$6::jsonb,$7)
           ON CONFLICT (provider, dedupe_key) WHERE dedupe_key IS NOT NULL DO NOTHING
           RETURNING id""",
        provider, event_type, dedupe_key, signature_valid,
        json.dumps(headers), json.dumps(payload, default=str), raw_body)
    return str(row["id"]) if row else None


async def receive_webhook(req: Request, background: BackgroundTasks, *,
                          provider: str, verifier: Verifier,
                          dedupe_from: Callable[[dict, bytes], str],
                          event_type_from: Callable[[dict], str]) -> dict:
    """Shared receiver: never blocks on processing, never 500s on bad payloads
    (store + mark failed instead — a webhook retry storm helps nobody)."""
    raw = await req.body()
    sig_ok = await verifier(req, raw)
    try:
        payload = json.loads(raw) if raw else {}
    except ValueError:
        payload = {}

    pool = get_pool()
    async with pool.acquire() as conn:
        inbox_id = await store_inbox(
            conn, provider=provider, event_type=event_type_from(payload),
            dedupe_key=dedupe_from(payload, raw), signature_valid=sig_ok,
            headers={k: v for k, v in req.headers.items()
                     if k.lower() in ("content-type", "user-agent", "x-request-id")},
            payload=payload, raw_body=raw.decode(errors="replace"))

    if inbox_id is None:
        return {"ok": True, "duplicate": True}
    if sig_ok is False:
        # Stored for forensics but never processed. 200 so the provider stops retrying;
        # alerting comes from the failed-row count, not from provider retry storms.
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE webhooks_inbox SET status='failed', error='bad signature' WHERE id=$1",
                inbox_id)
        log.error("%s webhook bad signature, inbox=%s", provider, inbox_id)
        return {"ok": True, "inbox_id": inbox_id}

    background.add_task(process_inbox_row, inbox_id)
    return {"ok": True, "inbox_id": inbox_id}


async def process_inbox_row(inbox_id: str) -> None:
    """Process one inbox row. Claims via status flip so a drainer worker and the
    inline background task never double-process."""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """UPDATE webhooks_inbox SET status='processing', attempts=attempts+1
               WHERE id=$1 AND status IN ('received','failed') AND attempts < 5
               RETURNING provider, event_type, payload""",
            inbox_id)
        if row is None:
            return
        try:
            handler = _HANDLERS.get(row["provider"])
            if handler:
                await handler(conn, row["event_type"], json.loads(row["payload"]))
            await conn.execute(
                "UPDATE webhooks_inbox SET status='processed', processed_at=now() WHERE id=$1",
                inbox_id)
        except Exception as e:                      # noqa: BLE001 — boundary; logged + persisted
            log.exception("inbox %s processing failed", inbox_id)
            await conn.execute(
                "UPDATE webhooks_inbox SET status='failed', error=$2 WHERE id=$1",
                inbox_id, str(e)[:500])


# ── per-provider processing (business logic; runs async) ────────────

async def _process_brevo(conn: asyncpg.Connection, event_type: str, payload: dict) -> None:
    email_addr = payload.get("email", "")
    mapping = {"opened": "email_opened", "click": "email_clicked",
               "delivered": "email_delivered"}
    if event_type in mapping:
        await repo.emit_event(conn, mapping[event_type],
                              payload={"email": email_addr}, source_system="brevo")
    elif event_type == "unsubscribe":
        await conn.execute("UPDATE customers SET consent_email=false WHERE email=$1", email_addr)
        await repo.emit_event(conn, "contact_unsubscribed",
                              payload={"email": email_addr, "channel": "email"},
                              source_system="brevo")


async def _process_gatewayapi(conn: asyncpg.Connection, event_type: str, payload: dict) -> None:
    msg_id = str(payload.get("id", ""))
    status = str(payload.get("status", "")).lower()
    if msg_id:
        await conn.execute(
            "UPDATE communication_logs SET status=$1 WHERE provider_msg_id=$2", status, msg_id)
    if status == "delivered":
        await repo.emit_event(conn, "sms_delivered", payload={"provider_msg_id": msg_id},
                              source_system="gatewayapi")
    # Inbound MO message with STOP → revoke consent (GatewayAPI inbound uses 'message'+'msisdn').
    text = str(payload.get("message", "")).strip().upper()
    msisdn = payload.get("msisdn")
    if text in ("STOP", "UNSUBSCRIBE") and msisdn:
        await conn.execute("UPDATE customers SET consent_sms=false WHERE phone=$1", f"+{msisdn}")
        await repo.emit_event(conn, "contact_unsubscribed",
                              payload={"phone": f"+{msisdn}", "channel": "sms"},
                              source_system="gatewayapi")


_HANDLERS = {"brevo": _process_brevo, "gatewayapi": _process_gatewayapi}


# ── example wired endpoint ───────────────────────────────────────────

async def _verify_brevo(req: Request, raw: bytes) -> Optional[bool]:
    """Brevo has no HMAC; use a shared-secret query param (?token=) set in the
    Brevo webhook URL. None would mean 'unsigned accepted' — we require the token."""
    expected = config.BREVO_WEBHOOK_TOKEN
    if not expected:
        return None
    return hmac.compare_digest(req.query_params.get("token", ""), expected)


@router.post("/brevo")
async def brevo_webhook(req: Request, background: BackgroundTasks) -> dict:
    return await receive_webhook(
        req, background, provider="brevo", verifier=_verify_brevo,
        dedupe_from=lambda p, raw: str(p.get("id") or hashlib.md5(raw).hexdigest()),
        event_type_from=lambda p: str(p.get("event", "unknown")))
