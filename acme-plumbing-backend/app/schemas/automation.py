"""n8n-facing lifecycle automation payloads (appointment reminders, delivery
posts, event callbacks). All /automations/* routes are INTERNAL_API_TOKEN gated.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DueAppointmentReminder(BaseModel):
    """A booking that is inside the reminder window and has not been reminded yet."""

    booking_id: uuid.UUID
    brand_id: uuid.UUID
    contact_id: uuid.UUID
    scheduled_for: datetime
    timezone: str
    first_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    service_address: dict = Field(default_factory=dict)


class DeliveryUpdateRequest(BaseModel):
    """Manual/relayed delivery outcome for a specific communication_logs row.
    `status` is a provider-native event name; it is mapped canonically server-side."""

    provider: str = Field(min_length=1, max_length=50)
    status: str = Field(min_length=1, max_length=100)      # provider event/status
    external_message_id: Optional[str] = Field(default=None, max_length=255)
    occurred_at: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)


class DeliveryUpdateOut(BaseModel):
    communication_log_id: uuid.UUID
    delivery_status: str
    event_name: str
    updated: bool


class AckResponse(BaseModel):
    ok: bool = True
    detail: Optional[str] = None
