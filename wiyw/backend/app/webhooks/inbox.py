"""Webhook inbox machinery: verify signature → store raw → 200 fast → process async.

Receivers call receive_webhook() with a provider-specific verifier + dedupe extractor
(see routes.py). Processing runs in a BackgroundTask; failed rows (attempts < 5) can be
re-claimed by a scheduled drainer hitting process_inbox_row again — the status-flip claim
in models/inbox.py makes the two race-safe.
"""
import json
import logging
from typing import Awaitable, Callable, Optional
from urllib.parse import parse_qs

import asyncpg
from fastapi import BackgroundTasks, Request

from ..db.session import get_pool
from ..models import inbox as inbox_repo
from ..models import repo

log = logging.getLogger("wiyw.inbox")

Verifier = Callable[[Request, bytes], Awaitable[Optional[bool]]]  # None = provider unsigned
Handler = Callable[[asyncpg.Connection, str, dict], Awaitable[None]]

_HANDLERS: dict[str, Handler] = {}


def register_handler(provider: str, handler: Handler) -> None:
    _HANDLERS[provider] = handler


def parse_body(raw: bytes, content_type: str) -> dict:
    """Best-effort parse: JSON first, then form-encoded (Mailgun legacy webhooks)."""
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"_body": parsed}
    except ValueError:
        pass
    if "form" in content_type or "urlencoded" in content_type:
        return {k: v[0] if len(v) == 1 else v
                for k, v in parse_qs(raw.decode(errors="replace")).items()}
    return {}


async def receive_webhook(req: Request, background: BackgroundTasks, *,
                          provider: str, verifier: Verifier,
                          dedupe_from: Callable[[dict, bytes], Optional[str]],
                          event_type_from: Callable[[dict], str]) -> dict:
    """Shared receiver: never blocks on processing, never 500s on bad payloads
    (store + mark failed instead — a provider retry storm helps nobody)."""
    raw = await req.body()
    sig_ok = await verifier(req, raw)
    payload = parse_body(raw, req.headers.get("content-type", ""))

    pool = get_pool()
    async with pool.acquire() as conn:
        inbox_id = await inbox_repo.store_inbox(
            conn, provider=provider, event_type=event_type_from(payload),
            dedupe_key=dedupe_from(payload, raw), signature_valid=sig_ok,
            headers={k: v for k, v in req.headers.items()
                     if k.lower() in ("content-type", "user-agent", "x-request-id",
                                      "svix-id", "svix-timestamp")},
            payload=payload, raw_body=raw.decode(errors="replace"))

    if inbox_id is None:
        return {"ok": True, "duplicate": True}
    if sig_ok is False:
        # Stored for forensics but never processed. 200 so the provider stops retrying;
        # alerting keys off failed-row counts, not provider retry storms.
        async with pool.acquire() as conn:
            await inbox_repo.mark_failed(conn, inbox_id, "bad signature")
        log.error("%s webhook bad signature, inbox=%s", provider, inbox_id)
        return {"ok": True, "inbox_id": inbox_id}

    background.add_task(process_inbox_row, inbox_id)
    return {"ok": True, "inbox_id": inbox_id}


async def process_inbox_row(inbox_id: str) -> None:
    """Process one inbox row (claimed via status flip; bounded attempts)."""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await inbox_repo.claim_for_processing(conn, inbox_id)
        if row is None:
            return
        try:
            handler = _HANDLERS.get(row["provider"])
            if handler:
                await handler(conn, row["event_type"], json.loads(row["payload"]))
            await inbox_repo.mark_processed(conn, inbox_id)
        except Exception as e:              # noqa: BLE001 — boundary; logged + persisted
            log.exception("inbox %s processing failed", inbox_id)
            await inbox_repo.mark_failed(conn, inbox_id, str(e))


# ── per-provider processors (business logic; run async off the request) ─

async def process_brevo(conn: asyncpg.Connection, event_type: str, payload: dict) -> None:
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


async def process_gatewayapi(conn: asyncpg.Connection, event_type: str, payload: dict) -> None:
    msg_id = str(payload.get("id", ""))
    status = str(payload.get("status", "")).lower()
    if msg_id and status:
        await conn.execute(
            "UPDATE communication_logs SET status=$1 WHERE provider_msg_id=$2", status, msg_id)
    if status == "delivered":
        await repo.emit_event(conn, "sms_delivered", payload={"provider_msg_id": msg_id},
                              source_system="gatewayapi")
    # Inbound MO message: honor STOP → revoke SMS consent.
    text = str(payload.get("message", "")).strip().upper()
    msisdn = payload.get("msisdn")
    if text in ("STOP", "UNSUBSCRIBE") and msisdn:
        await conn.execute("UPDATE customers SET consent_sms=false WHERE phone=$1", f"+{msisdn}")
        await repo.emit_event(conn, "contact_unsubscribed",
                              payload={"phone": f"+{msisdn}", "channel": "sms"},
                              source_system="gatewayapi")


async def process_resend(conn: asyncpg.Connection, event_type: str, payload: dict) -> None:
    data = payload.get("data", {})
    email_id = str(data.get("email_id", ""))
    status = event_type.replace("email.", "")
    if email_id:
        await conn.execute(
            "UPDATE communication_logs SET status=$1 WHERE provider_msg_id=$2",
            status, email_id)
    mapping = {"delivered": "email_delivered", "opened": "email_opened",
               "clicked": "email_clicked"}
    if status in mapping:
        await repo.emit_event(conn, mapping[status],
                              payload={"provider_msg_id": email_id}, source_system="backend")


async def process_mailgun(conn: asyncpg.Connection, event_type: str, payload: dict) -> None:
    # JSON delivery events carry event-data; legacy form posts carry flat fields.
    event_data = payload.get("event-data", {})
    msg_id = str(event_data.get("message", {}).get("headers", {}).get("message-id", "")
                 or payload.get("Message-Id", ""))
    event = str(event_data.get("event", event_type or "")).lower()
    if msg_id and event in ("delivered", "failed", "complained"):
        await conn.execute(
            "UPDATE communication_logs SET status=$1 WHERE provider_msg_id=$2", event, msg_id)
    if event == "delivered":
        await repo.emit_event(conn, "email_delivered",
                              payload={"provider_msg_id": msg_id}, source_system="backend")
    # Inbound parse (reply email): log it; owner notification handled by ops for now.
    if payload.get("sender") and payload.get("body-plain"):
        await repo.log_comm(conn, channel="email", direction="inbound",
                            to_addr=str(payload.get("recipient", "")),
                            provider="mailgun", template="inbound_reply",
                            status="received")


async def process_storyblok(conn: asyncpg.Connection, event_type: str, payload: dict) -> None:
    story_id = str(payload.get("story_id", ""))
    action = str(payload.get("action", event_type or ""))
    full_slug = str(payload.get("full_slug", "") or payload.get("slug", ""))
    if story_id and full_slug and action in ("published", "unpublished"):
        status = "published" if action == "published" else "archived"
        await conn.execute(
            """INSERT INTO content_pages (storyblok_story_id, slug, status, published_at)
               VALUES ($1, $2, $3, CASE WHEN $3='published' THEN now() END)
               ON CONFLICT (brand_id, slug) DO UPDATE
                 SET storyblok_story_id=EXCLUDED.storyblok_story_id,
                     status=EXCLUDED.status,
                     published_at=COALESCE(EXCLUDED.published_at, content_pages.published_at)""",
            story_id, full_slug, status)
    log.info("Storyblok %s for %s; sitemap rebuild queued", action, full_slug)
    # TODO: enqueue sitemap regen + GSC sitemap ping (Next.js revalidate hook)


register_handler("brevo", process_brevo)
register_handler("gatewayapi", process_gatewayapi)
register_handler("resend", process_resend)
register_handler("mailgun", process_mailgun)
register_handler("storyblok", process_storyblok)
