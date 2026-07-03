"""Booking + job schemas."""
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


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


class BookingOut(BaseModel):
    id: str
    customer_id: str
    lead_id: Optional[str]
    scheduled_for: datetime
    service_type: str
    status: BookingStatus
    reminder_24h_sent: bool
    reminder_2h_sent: bool
    created_at: datetime


class JobIn(BaseModel):
    booking_id: Optional[str] = None
    customer_id: str
    service_type: str = Field(min_length=1, max_length=50)
    amount: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = Field(default=None, max_length=4000)


class JobComplete(BaseModel):
    amount: float = Field(ge=0)
    completed_at: Optional[datetime] = None
