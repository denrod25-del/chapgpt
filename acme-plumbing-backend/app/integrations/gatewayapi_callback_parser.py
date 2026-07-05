"""GatewayAPI (and generic) SMS delivery-callback parsing.

Callback shape varies by GatewayAPI configuration, so this parser is defensive:
it pulls common fields when present and never raises on a partial/odd payload.
GatewayAPI DLRs commonly look like:
  {"id": 123456, "msisdn": 4512345678, "status": "DELIVERED", "time": 1699999999}
There is no cryptographic signature; verification is a scaffold that returns
'unverified' (secure the endpoint with a URL token / network policy instead).
"""
from datetime import datetime, timezone
from typing import Any, Optional

# Fields we look at, in priority order, for each logical value.
_ID_KEYS = ("id", "message_id", "messageid", "msg_id", "mid")
_STATUS_KEYS = ("status", "state", "dlr_status", "delivery_status")
_PHONE_KEYS = ("msisdn", "to", "recipient", "number", "phone")
_TIME_KEYS = ("time", "timestamp", "ts", "received")


def _first(payload: dict, keys: tuple[str, ...]) -> Optional[Any]:
    for k in keys:
        if payload.get(k) not in (None, ""):
            return payload[k]
    return None


def _to_phone(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    # GatewayAPI sends bare international digits; normalize to E.164 best-effort.
    return s if s.startswith("+") else f"+{s}"


def _to_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    try:
        # Epoch seconds (int/str) is the common GatewayAPI form.
        return datetime.fromtimestamp(int(value), tz=timezone.utc)
    except (ValueError, TypeError, OSError):
        pass
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


class ParsedSmsCallback:
    __slots__ = ("external_message_id", "status", "phone", "occurred_at")

    def __init__(
        self,
        external_message_id: Optional[str],
        status: Optional[str],
        phone: Optional[str],
        occurred_at: Optional[datetime],
    ) -> None:
        self.external_message_id = external_message_id
        self.status = status
        self.phone = phone
        self.occurred_at = occurred_at


def parse(payload: dict) -> ParsedSmsCallback:
    """Extract the common DLR fields. Missing fields come back as None."""
    if not isinstance(payload, dict):
        return ParsedSmsCallback(None, None, None, None)
    raw_id = _first(payload, _ID_KEYS)
    raw_status = _first(payload, _STATUS_KEYS)
    return ParsedSmsCallback(
        external_message_id=str(raw_id) if raw_id is not None else None,
        status=str(raw_status).strip() if raw_status is not None else None,
        phone=_to_phone(_first(payload, _PHONE_KEYS)),
        occurred_at=_to_dt(_first(payload, _TIME_KEYS)),
    )


def verification_status(payload: dict) -> str:
    """No signature scheme for GatewayAPI callbacks — always 'unverified'.
    (Protect the route with a shared URL token / IP allowlist at the edge.)"""
    return "unverified"
