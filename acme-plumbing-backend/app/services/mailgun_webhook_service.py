"""Parse a raw Mailgun webhook into canonical NormalizedEvents.

Mailgun posts one event per request under `event-data`. Verification is delegated
to mailgun_webhook_verifier (HMAC-SHA256 of timestamp+token).
"""
from datetime import datetime, timezone
from typing import Optional

from app.integrations import mailgun_webhook_verifier
from app.schemas.provider_events import (
    NormalizedEvent,
    channel_for,
    map_provider_event,
)

_PROVIDER = "mailgun"


def verification_status(payload: dict) -> str:
    return mailgun_webhook_verifier.verification_status(payload)


def _message_id(event_data: dict) -> Optional[str]:
    headers = event_data.get("message", {}).get("headers", {}) if event_data else {}
    mid = headers.get("message-id")
    if mid:
        # We may have stored the send id with or without angle brackets.
        return str(mid).strip("<>")
    return None


def _timestamp(event_data: dict) -> Optional[datetime]:
    ts = event_data.get("timestamp")
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc) if ts else None
    except (ValueError, TypeError, OSError):
        return None


def parse_events(payload: dict) -> list[NormalizedEvent]:
    event_data = payload.get("event-data") or {}
    if not isinstance(event_data, dict) or not event_data.get("event"):
        return []

    provider_event = str(event_data.get("event"))
    severity = event_data.get("severity")
    canonical_event, delivery_status, flags = map_provider_event(
        _PROVIDER, provider_event, severity=severity
    )
    tags = event_data.get("tags") if isinstance(event_data.get("tags"), list) else []

    return [
        NormalizedEvent(
            provider=_PROVIDER,
            provider_event=provider_event,
            canonical_event=canonical_event,
            delivery_status=delivery_status,
            channel=channel_for(_PROVIDER),
            external_message_id=_message_id(event_data),
            email=event_data.get("recipient"),
            tags=[str(t) for t in tags],
            is_bounce="b" in flags,
            is_complaint="c" in flags,
            is_unsubscribe="u" in flags,
            occurred_at=_timestamp(event_data),
            raw=event_data,
        )
    ]
