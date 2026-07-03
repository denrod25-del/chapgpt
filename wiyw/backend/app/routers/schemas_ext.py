"""Extended schemas (Section 12) — bookings, jobs, quotes, reviews, webhooks."""
import re
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator

E164 = re.compile(r"^\+[1-9]\d{7,14}$")


class BookingStatus(str, Enum):
    scheduled = "scheduled"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"


class BookingIn(BaseModel):
    customer_id: str
    lead_id: Optional[str] = None
    scheduled_for: datetime
    service_type: str = Field(min_length=1, max_length=50)

    @field_validator("scheduled_for")
    @classmethod
    def _future(cls, v: datetime) -> datetime:
        # Bookings must be in the future at creation time.
        assert v.timestamp() > datetime.now().timestamp() - 60, "scheduled_for must be future"
        return v


class BookingStatusUpdate(BaseModel):
    status: BookingStatus


class JobIn(BaseModel):
    booking_id: Optional[str] = None
    customer_id: str
    service_type: str = Field(min_length=1, max_length=50)
    amount: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = Field(default=None, max_length=4000)


class JobComplete(BaseModel):
    amount: float = Field(ge=0)
    completed_at: Optional[datetime] = None


class QuoteIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    phone: str
    email: Optional[str] = None
    service_type: str = Field(min_length=1, max_length=50)
    details: Optional[str] = Field(default=None, max_length=2000)
    source: str = "website"

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        v = v.strip()
        assert E164.match(v), "phone must be E.164"
        return v


class ReviewIn(BaseModel):
    customer_id: Optional[str] = None
    job_id: Optional[str] = None
    rating: int = Field(ge=1, le=5)
    platform: str = Field(pattern="^(google|facebook|internal)$")
    content: Optional[str] = Field(default=None, max_length=4000)
