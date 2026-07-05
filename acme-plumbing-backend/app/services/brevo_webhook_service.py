"""Parse a raw Brevo webhook into canonical NormalizedEvents.

Brevo posts one transactional/marketing event per request. Identifiers seen in
documented payloads: `event`, `email`, `message-id`, `tags`, `subject`, `date`/`ts`.
Verification is delegated to brevo_webhook_verifier (shared secret; no HMAC).
"""
from datetime import datetime, timezone
from typing import Mapping, Optional

from app.integrations import brevo_webhook_verifier
from app.schemas.provider_events import (
    NormalizedEvent,
    channel_for,
    map_provider_event,
)

_PROVIDER = "brevo"


def verification_status(headers: Mapping[str, str], payload: dict) -> str:
    return brevo_webhook_verifier.verification_status(headers, payload)


def _tags(payload: dict) -> list[str]:
    tags = payload.get("tags")
    if isinstance(tags, list):
        return [str(t) for t in tags]
    if isinstance(tags, str) and tags:
        return [tags]
    return []


def _timestamp(payload: dict) -> Optional[datetime]:
    ts = payload.get("ts") or payload.get("ts_event")
    if ts:
        try:
            return datetime.fromtimestamp(float(ts), tz=timezone.utc)
        except (ValueError, TypeError, OSError):
            pass
    date = payload.get("date")
    if date:
        try:
            return datetime.fromisoformat(str(date))
        except ValueError:
            return None
    return None


def parse_events(payload: dict) -> list[NormalizedEvent]:
    provider_event = payload.get("event")
    if not provider_event:
        return []

    canonical_event, delivery_status, flags = map_provider_event(_PROVIDER, str(provider_event))
    mid = payload.get("message-id") or payload.get("messageId")

    return [
        NormalizedEvent(
            provider=_PROVIDER,
            provider_event=str(provider_event),
            canonical_event=canonical_event,
            delivery_status=delivery_status,
            channel=channel_for(_PROVIDER),
            external_message_id=str(mid) if mid else None,
            email=payload.get("email"),
            tags=_tags(payload),
            is_bounce="b" in flags,
            is_complaint="c" in flags,
            is_unsubscribe="u" in flags,
            occurred_at=_timestamp(payload),
            raw=payload,
        )
    ]
