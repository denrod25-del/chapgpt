"""Canonical provider-event vocabulary + the mapping layer.

This is the single source of truth for how raw Brevo / Mailgun / GatewayAPI
events collapse into (a) a canonical `communication_logs.delivery_status` and
(b) a canonical `event_log.event_name`. Provider services parse identifiers off
the raw payload and hand a `NormalizedEvent` to delivery_reconciliation_service.
"""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DeliveryStatus(str, Enum):
    """Canonical delivery states. Mirrors the communication_logs CHECK constraint
    added in migration 002. Ordered loosely by lifecycle progression."""

    queued = "queued"
    sent = "sent"
    delivered = "delivered"
    opened = "opened"
    clicked = "clicked"
    deferred = "deferred"
    soft_bounce = "soft_bounce"
    blocked = "blocked"
    hard_bounce = "hard_bounce"
    failed = "failed"
    bounced = "bounced"          # legacy generic bounce (kept for back-compat)
    complaint = "complaint"
    unsubscribed = "unsubscribed"


# Forward-progress rank. Reconciliation only advances delivery_status to a higher
# rank, except for "negative" signals which always apply (a late bounce/complaint
# must win even if a 'delivered' already landed).
_RANK: dict[str, int] = {
    "queued": 0,
    "sent": 1,
    "deferred": 1,
    "delivered": 2,
    "opened": 2,
    "clicked": 2,
    "soft_bounce": 3,
    "blocked": 3,
    "hard_bounce": 4,
    "failed": 4,
    "bounced": 4,
    "complaint": 5,
    "unsubscribed": 5,
}

_NEGATIVE: frozenset[str] = frozenset(
    {"soft_bounce", "hard_bounce", "failed", "bounced", "complaint",
     "unsubscribed", "blocked", "deferred"}
)


def should_apply_status(current: Optional[str], incoming: str) -> bool:
    """True if `incoming` should overwrite `current` on a communication_logs row.
    Negative/terminal signals always apply; progress signals only move forward."""
    if incoming in _NEGATIVE:
        return True
    if current is None:
        return True
    return _RANK.get(incoming, 0) > _RANK.get(current, -1)


# ── canonical event names (event_log.event_name) ────────────────────────────
# Lifecycle + system events. Keep in sync with docs/event-taxonomy and n8n.
class EventName(str, Enum):
    lead_created = "lead_created"
    booking_created = "booking_created"
    booking_confirmed = "booking_confirmed"
    appointment_reminder_due = "appointment_reminder_due"
    appointment_reminder_sent = "appointment_reminder_sent"
    review_request_scheduled = "review_request_scheduled"
    review_request_sent = "review_request_sent"
    review_request_delivered = "review_request_delivered"
    review_request_clicked = "review_request_clicked"
    review_request_completed = "review_request_completed"
    review_request_failed = "review_request_failed"
    email_sent = "email_sent"
    email_delivered = "email_delivered"
    email_opened = "email_opened"
    email_clicked = "email_clicked"
    email_soft_bounced = "email_soft_bounced"
    email_hard_bounced = "email_hard_bounced"
    email_deferred = "email_deferred"
    email_blocked = "email_blocked"
    email_failed = "email_failed"
    sms_sent = "sms_sent"
    sms_delivered = "sms_delivered"
    sms_failed = "sms_failed"
    sms_clicked = "sms_clicked"
    contact_unsubscribed = "contact_unsubscribed"
    complaint_received = "complaint_received"
    webhook_unmatched = "webhook_unmatched"


class NormalizedEvent(BaseModel):
    """One provider event, collapsed to canonical terms. `delivery_status=None`
    means 'log the event but do not change the row's delivery_status' (opens,
    clicks)."""

    provider: str
    provider_event: str
    canonical_event: str
    delivery_status: Optional[str] = None
    channel: str = "email"                      # email | sms
    external_message_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    is_bounce: bool = False
    is_complaint: bool = False
    is_unsubscribe: bool = False
    occurred_at: Optional[datetime] = None
    raw: dict = Field(default_factory=dict)


# ── provider → canonical maps ───────────────────────────────────────────────
# Each entry: provider_event -> (canonical_event, delivery_status|None, flags)
# flags: b=bounce, c=complaint, u=unsubscribe

_EMAIL = "email"
_SMS = "sms"

# Brevo transactional/marketing event names.
BREVO_MAP: dict[str, tuple[str, Optional[str], str]] = {
    "request": (EventName.email_sent, DeliveryStatus.sent, ""),
    "sent": (EventName.email_sent, DeliveryStatus.sent, ""),
    "delivered": (EventName.email_delivered, DeliveryStatus.delivered, ""),
    "opened": (EventName.email_opened, None, ""),
    "uniqueOpened": (EventName.email_opened, None, ""),
    "click": (EventName.email_clicked, None, ""),
    "softBounce": (EventName.email_soft_bounced, DeliveryStatus.soft_bounce, "b"),
    "hardBounce": (EventName.email_hard_bounced, DeliveryStatus.hard_bounce, "b"),
    "invalid": (EventName.email_hard_bounced, DeliveryStatus.hard_bounce, "b"),
    "invalid_email": (EventName.email_hard_bounced, DeliveryStatus.hard_bounce, "b"),
    "deferred": (EventName.email_deferred, DeliveryStatus.deferred, ""),
    "blocked": (EventName.email_blocked, DeliveryStatus.blocked, ""),
    "spam": (EventName.complaint_received, DeliveryStatus.complaint, "c"),
    "unsubscribed": (EventName.contact_unsubscribed, DeliveryStatus.unsubscribed, "u"),
    "error": (EventName.email_failed, DeliveryStatus.failed, ""),
}

# Mailgun event names (event-data.event; 'failed' disambiguated by severity).
MAILGUN_MAP: dict[str, tuple[str, Optional[str], str]] = {
    "accepted": (EventName.email_sent, DeliveryStatus.sent, ""),
    "delivered": (EventName.email_delivered, DeliveryStatus.delivered, ""),
    "opened": (EventName.email_opened, None, ""),
    "clicked": (EventName.email_clicked, None, ""),
    "unsubscribed": (EventName.contact_unsubscribed, DeliveryStatus.unsubscribed, "u"),
    "complained": (EventName.complaint_received, DeliveryStatus.complaint, "c"),
    "permanent_fail": (EventName.email_hard_bounced, DeliveryStatus.hard_bounce, "b"),
    "temporary_fail": (EventName.email_deferred, DeliveryStatus.deferred, ""),
    "rejected": (EventName.email_failed, DeliveryStatus.failed, ""),
}

# GatewayAPI / generic SMS delivery states (upper-cased before lookup).
GATEWAYAPI_MAP: dict[str, tuple[str, Optional[str], str]] = {
    "DELIVERED": (EventName.sms_delivered, DeliveryStatus.delivered, ""),
    "ACCEPTED": (EventName.sms_sent, DeliveryStatus.sent, ""),
    "BUFFERED": (EventName.sms_sent, DeliveryStatus.sent, ""),
    "ENROUTE": (EventName.sms_sent, DeliveryStatus.sent, ""),
    "QUEUED": (EventName.sms_sent, DeliveryStatus.sent, ""),
    "UNDELIVERABLE": (EventName.sms_failed, DeliveryStatus.failed, ""),
    "UNDELIVERED": (EventName.sms_failed, DeliveryStatus.failed, ""),
    "REJECTED": (EventName.sms_failed, DeliveryStatus.failed, ""),
    "EXPIRED": (EventName.sms_failed, DeliveryStatus.failed, ""),
    "FAILED": (EventName.sms_failed, DeliveryStatus.failed, ""),
    "CLICKED": (EventName.sms_clicked, None, ""),
}


def map_provider_event(
    provider: str, provider_event: Optional[str], *, severity: Optional[str] = None
) -> tuple[str, Optional[str], str]:
    """Return (canonical_event, delivery_status|None, flagstr) for a raw event.
    Unknown events collapse to a generic '<channel>_status_unknown'-style row so
    processing never crashes on an unrecognized provider event."""
    ev = (provider_event or "").strip()
    if provider == "brevo":
        if ev in BREVO_MAP:
            return BREVO_MAP[ev]
        return (f"email_{ev or 'unknown'}", None, "")
    if provider == "mailgun":
        # Mailgun collapses hard/soft under a single 'failed' event + severity.
        if ev == "failed":
            if (severity or "").lower() == "permanent":
                return MAILGUN_MAP["permanent_fail"]
            return MAILGUN_MAP["temporary_fail"]
        if ev in MAILGUN_MAP:
            return MAILGUN_MAP[ev]
        return (f"email_{ev or 'unknown'}", None, "")
    if provider == "gatewayapi":
        key = ev.upper()
        if key in GATEWAYAPI_MAP:
            return GATEWAYAPI_MAP[key]
        return (f"sms_{ev.lower() or 'unknown'}", None, "")
    return (f"{provider}_{ev or 'unknown'}", None, "")


def channel_for(provider: str) -> str:
    return _SMS if provider == "gatewayapi" else _EMAIL
