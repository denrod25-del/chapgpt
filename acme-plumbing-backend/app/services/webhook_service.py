"""Webhook intake: store raw payload in webhook_inbox, ack fast.

Scaffolded, deliberately not fully implemented:
- TODO(signature): verify provider signatures BEFORE trusting payloads —
  Mailgun: HMAC-SHA256 of timestamp+token with the API signing key;
  Brevo / GatewayAPI: no native HMAC — require a shared token in the webhook URL.
- TODO(processing): move row processing to background work (FastAPI
  BackgroundTasks or a worker) that claims rows via processing_status flips
  ('received' → 'processing' → 'processed'/'failed') and sets processed_at.
"""
import hashlib
import json
from typing import Callable, Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import webhook_repository
from app.schemas.webhook import WebhookReceiptResponse

_KEPT_HEADERS = ("content-type", "user-agent", "x-request-id")

# Per-provider extraction of a stable dedupe key and event type from the payload.
_DEDUPE_EXTRACTORS: dict[str, Callable[[dict], Optional[str]]] = {
    "brevo": lambda p: str(p["id"]) if p.get("id") else None,
    "mailgun": lambda p: (p.get("signature") or {}).get("token"),
    # One delivery report per (message id, state).
    "gatewayapi": lambda p: f"{p['id']}:{p.get('status', '')}" if p.get("id") else None,
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
    """Raw signature for later verification/forensics. Mailgun's JSON webhooks
    carry it in the body (signature.signature), not a header."""
    header_sig = request.headers.get(_SIGNATURE_HEADERS.get(provider, ""), None)
    if header_sig:
        return header_sig
    if provider == "mailgun":
        return (payload.get("signature") or {}).get("signature")
    return None


async def receive_webhook(
    db: AsyncSession, provider: str, request: Request
) -> WebhookReceiptResponse:
    """Store the raw webhook and return immediately. Never does business work
    in the request path; duplicates die at the unique index, not in code."""
    raw = await request.body()
    try:
        payload = json.loads(raw) if raw else {}
    except ValueError:
        payload = {}
    if not isinstance(payload, dict):
        payload = {"_body": payload}

    # TODO(signature): verify before storing signature_valid-style state; for now
    # the raw signature is stored for later verification/forensics.
    signature = _extract_signature(provider, request, payload)

    dedupe_key = _DEDUPE_EXTRACTORS.get(provider, lambda p: None)(payload)
    if dedupe_key is None:
        dedupe_key = hashlib.sha256(raw).hexdigest()

    inbox_id = await webhook_repository.store(
        db,
        provider=provider,
        event_type=_EVENT_TYPE_EXTRACTORS.get(provider, lambda p: None)(payload),
        signature=signature,
        headers_json={k: v for k, v in request.headers.items() if k.lower() in _KEPT_HEADERS},
        payload_json=payload,
        dedupe_key=dedupe_key,
    )
    await db.commit()

    if inbox_id is None:
        return WebhookReceiptResponse(ok=True, duplicate=True)

    # TODO(processing): background.add_task(process_inbox_row, inbox_id)
    return WebhookReceiptResponse(ok=True, inbox_id=inbox_id)
