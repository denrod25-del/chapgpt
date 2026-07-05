"""Review-request scheduling payloads (n8n lifecycle automation).

A review request is a scheduled outbound ask (SMS/email) for a Google/GBP review,
created when a job/booking completes and dispatched by n8n once it is due.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewRequestCreate(BaseModel):
    brand_slug: str = Field(default="acme-plumbing", min_length=1, max_length=100)
    contact_id: uuid.UUID
    lead_id: Optional[uuid.UUID] = None
    booking_id: Optional[uuid.UUID] = None
    channel: str = Field(default="sms", pattern="^(sms|email)$")
    review_url: Optional[str] = Field(default=None, max_length=1000)  # default: settings.DEFAULT_REVIEW_URL
    scheduled_for: Optional[datetime] = None                          # default: now + delay
    delay_minutes: Optional[int] = Field(default=None, ge=0, le=60 * 24 * 30)
    metadata: dict = Field(default_factory=dict)


class ReviewRequestOut(BaseModel):
    """Full review-request record."""

    id: uuid.UUID
    brand_id: uuid.UUID
    contact_id: uuid.UUID
    lead_id: Optional[uuid.UUID]
    booking_id: Optional[uuid.UUID]
    communication_log_id: Optional[uuid.UUID]
    channel: str
    status: str
    review_url: str
    scheduled_for: datetime
    sent_at: Optional[datetime]
    completed_at: Optional[datetime]
    failure_reason: Optional[str]
    created_at: datetime


class DueReviewRequest(BaseModel):
    """Trimmed view for n8n send nodes: everything needed to dispatch one ask."""

    id: uuid.UUID
    brand_id: uuid.UUID
    contact_id: uuid.UUID
    channel: str
    review_url: str
    scheduled_for: datetime
    first_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


class MarkSentRequest(BaseModel):
    external_message_id: Optional[str] = Field(default=None, max_length=255)
    communication_log_id: Optional[uuid.UUID] = None
    provider: Optional[str] = Field(default=None, max_length=50)


class MarkFailedRequest(BaseModel):
    failure_reason: str = Field(min_length=1, max_length=1000)


class MarkCompletedRequest(BaseModel):
    completed_at: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)


class ReviewRequestActionOut(BaseModel):
    id: uuid.UUID
    status: str
    updated: bool = True
