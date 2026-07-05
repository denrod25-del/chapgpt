"""Inbound webhook intake + inline reconciliation.

Flow per request:
  1. Read raw body/headers; parse JSON defensively (never raise on bad JSON).
  2. Compute a stable dedupe key and provider event type.
  3. Verify authenticity (Mailgun HMAC; Brevo shared secret; GatewayAPI scaffold).
  4. Store the raw payload in webhook_inbox and COMMIT — receipt is durable even
     if later processing fails; duplicates die at the (provider, dedupe_key) index.
  5. If processing is enabled and verification didn't fail, parse the payload into
     canonical events and reconcile each into communication_logs / event_log.
  6. Mark the inbox row processed/failed and COMMIT.

Nothing in the processing path is allowed to crash the endpoint: failures are
recorded on the inbox row and returned as processing_status='failed'.
"""
import hashlib
import json
from typing import Callable, Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories import webhook_repository
from app.schemas.provider_events import NormalizedEvent
from app.schemas.webhook import WebhookReceiptResponse
from app.services import (
    brevo_webhook_service,
    delivery_reconciliation_service,
    gatewayapi_webhook_service,
    mailgun_webhook_service,
)

_KEPT_HEADERS = (
    "content-type", "user-agent", "x-request-id",
    "x-mailgun-signature", "x-sib-signature",
    "x-sib-webhook-secret", "x-brevo-webhook-secret", "x-webhook-secret",
)


def _brevo_dedupe(p: dict) -> Optional[str]:
    """A single Brevo message emits many events (delivered, opened, click, …) that
    all share the same `id` / `message-id`. Keying on the identifier alone would
    drop every event after the first as a duplicate, so the event type is part of
    the key. Retries of the *same* event still dedupe (same event + identifier)."""
    ident = p.get("message-id") or p.get("id")
    if ident is None:
        return None
    return f"{p.get('event') or 'event'}:{ident}"


def _mailgun_dedupe(p: dict) -> Optional[str]:
    # The signature token is unique per webhook POST; Mailgun reuses it on retry,
    # so it dedupes retries while distinguishing separate events.
    token = (p.get("signature") or {}).get("token")
    if token:
        return token
    event_id = (p.get("event-data") or {}).get("id")
    return str(event_id) if event_id else None


def _gatewayapi_dedupe(p: dict) -> Optional[str]:
    # One delivery report per (message id, delivery state).
    return f"{p['id']}:{p.get('status', '')}" if p.get("id") else None


_DEDUPE_EXTRACTORS: dict[str, Callable[[dict], Optional[str]]] = {
    "brevo": _brevo_dedupe,
    "mailgun": _mailgun_dedupe,
    "gatewayapi": _gatewayapi_dedupe,
}

_EVENT_TYPE_EXTRACTORS: dict[str, Callable[[dict], Optional[str]]] = {
    "brevo": lambda p: p.get("event"),
    "mailgun": lambda p: (p.get("event-data") or {}).get("event"),
    "gatewayapi": lambda p: str(p.get("status") or "").lower() or None,
}

_SIGNATURE_HEADERS: dict[str, str] = {
    "mailgun": "x-mailgun-signature",
    "brevo": "x-sib-signature",
    "gatewayapi": "x-gwapi-signature",
}


def _extract_signature(provider: str, request: Request, payload: dict) -> Optional[str]:
    header_sig = request.headers.get(_SIGNATURE_HEADERS.get(provider, ""), None)
    if header_sig:
        return header_sig
    if provider == "mailgun":
        return (payload.get("signature") or {}).get("signature")
    return None


def _verification_status(provider: str, headers, payload: dict) -> str:
    if provider == "mailgun":
        return mailgun_webhook_service.verification_status(payload)
    if provider == "brevo":
        return brevo_webhook_service.verification_status(headers, payload)
    if provider == "gatewayapi":
        return gatewayapi_webhook_service.verification_status(payload)
    return "unverified"


def _parse_events(provider: str, payload: dict) -> list[NormalizedEvent]:
    if provider == "mailgun":
        return mailgun_webhook_service.parse_events(payload)
    if provider == "brevo":
        return brevo_webhook_service.parse_events(payload)
    if provider == "gatewayapi":
        return gatewayapi_webhook_service.parse_events(payload)
    return []


async def receive_webhook(
    db: AsyncSession, provider: str, request: Request
) -> WebhookReceiptResponse:
    raw = await request.body()
    try:
        payload = json.loads(raw) if raw else {}
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {"_body": payload}

    verification_status = _verification_status(provider, request.headers, payload)
    signature = _extract_signature(provider, request, payload)
    event_type = _EVENT_TYPE_EXTRACTORS.get(provider, lambda p: None)(payload)

    dedupe_key = _DEDUPE_EXTRACTORS.get(provider, lambda p: None)(payload)
    if dedupe_key is None:
        dedupe_key = hashlib.sha256(raw).hexdigest()

    # 1. persist raw receipt first (durable), then process.
    inbox_id = await webhook_repository.store(
        db,
        provider=provider,
        event_type=event_type,
        signature=signature,
        headers_json={k: v for k, v in request.headers.items() if k.lower() in _KEPT_HEADERS},
        payload_json=payload,
        dedupe_key=dedupe_key,
        verification_status=verification_status,
    )
    await db.commit()

    if inbox_id is None:
        # Already seen: acknowledge without re-applying side effects.
        return WebhookReceiptResponse(
            ok=True, duplicate=True, event_type=event_type,
            verification_status=verification_status, processing_status="skipped",
        )

    if not settings.ENABLE_WEBHOOK_PROCESSING:
        return WebhookReceiptResponse(
            ok=True, inbox_id=inbox_id, event_type=event_type,
            verification_status=verification_status, processing_status=None,
        )

    if verification_status == "invalid":
        # Stored for forensics, but its side effects are NOT applied.
        await webhook_repository.mark_processed(
            db, inbox_id, error_message="verification=invalid; side effects skipped"
        )
        await db.commit()
        return WebhookReceiptResponse(
            ok=True, inbox_id=inbox_id, event_type=event_type,
            verification_status=verification_status, processing_status="processed",
        )

    # 2. parse + reconcile; never let a bad payload crash the endpoint.
    applied = 0
    try:
        for normalized in _parse_events(provider, payload):
            await delivery_reconciliation_service.reconcile(db, normalized)
            applied += 1
        await webhook_repository.mark_processed(db, inbox_id)
        await db.commit()
    except Exception as exc:  # noqa: BLE001 — record + swallow; ack must stay predictable
        await db.rollback()
        await webhook_repository.mark_failed(db, inbox_id, error_message=repr(exc))
        await db.commit()
        return WebhookReceiptResponse(
            ok=True, inbox_id=inbox_id, event_type=event_type,
            verification_status=verification_status, processing_status="failed",
        )

    return WebhookReceiptResponse(
        ok=True, inbox_id=inbox_id, event_type=event_type,
        verification_status=verification_status, processing_status="processed",
        applied=applied,
    )
