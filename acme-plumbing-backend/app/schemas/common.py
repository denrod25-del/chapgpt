"""Shared enums + small common schemas. Enum values match the SQL CHECK constraints."""
from enum import Enum

from pydantic import BaseModel


class LeadType(str, Enum):
    website_form = "website_form"
    quote_request = "quote_request"
    phone_call = "phone_call"
    chat = "chat"
    other = "other"


class LeadStatus(str, Enum):
    new = "new"
    contacted = "contacted"
    quoted = "quoted"
    won = "won"
    lost = "lost"


class Urgency(str, Enum):
    emergency = "emergency"
    standard = "standard"
    flexible = "flexible"


class BookingStatus(str, Enum):
    pending = "pending"
    scheduled = "scheduled"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"


class ProcessingStatus(str, Enum):
    received = "received"
    processing = "processing"
    processed = "processed"
    failed = "failed"
    skipped_duplicate = "skipped_duplicate"


class CommChannel(str, Enum):
    email = "email"
    sms = "sms"


class DeliveryStatus(str, Enum):
    queued = "queued"
    sent = "sent"
    delivered = "delivered"
    failed = "failed"
    bounced = "bounced"


class HealthResponse(BaseModel):
    status: str = "ok"
    app: str
    env: str
