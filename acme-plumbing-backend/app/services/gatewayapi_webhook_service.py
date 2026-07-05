"""Parse a raw GatewayAPI / generic SMS delivery callback into a NormalizedEvent.

Field extraction is delegated to gatewayapi_callback_parser (defensive). There is
no signature scheme, so verification_status is always 'unverified'.
"""
from app.integrations import gatewayapi_callback_parser
from app.schemas.provider_events import (
    NormalizedEvent,
    channel_for,
    map_provider_event,
)

_PROVIDER = "gatewayapi"


def verification_status(payload: dict) -> str:
    return gatewayapi_callback_parser.verification_status(payload)


def parse_events(payload: dict) -> list[NormalizedEvent]:
    parsed = gatewayapi_callback_parser.parse(payload)
    if parsed.status is None and parsed.external_message_id is None:
        return []

    canonical_event, delivery_status, _flags = map_provider_event(_PROVIDER, parsed.status)
    return [
        NormalizedEvent(
            provider=_PROVIDER,
            provider_event=parsed.status or "unknown",
            canonical_event=canonical_event,
            delivery_status=delivery_status,
            channel=channel_for(_PROVIDER),
            external_message_id=parsed.external_message_id,
            phone=parsed.phone,
            occurred_at=parsed.occurred_at,
            raw=payload if isinstance(payload, dict) else {"_raw": payload},
        )
    ]
