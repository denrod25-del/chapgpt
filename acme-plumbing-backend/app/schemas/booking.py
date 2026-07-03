import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.schemas.common import BookingStatus

E164 = re.compile(r"^\+[1-9]\d{7,14}$")


class BookingCreateRequest(BaseModel):
    brand_slug: str = Field(default="acme-plumbing", min_length=1, max_length=100)
    lead_id: Optional[uuid.UUID] = None
    first_name: str = Field(min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None                      # E.164
    scheduled_for: datetime
    timezone: Optional[str] = None                   # default: settings.DEFAULT_TIMEZONE
    service_address: dict = Field(default_factory=dict)
    notes: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("phone")
    @classmethod
    def _phone_e164(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        assert E164.match(v), "phone must be E.164 (e.g. +15615550123)"
        return v

    @field_validator("scheduled_for")
    @classmethod
    def _future(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        assert v > datetime.now(timezone.utc), "scheduled_for must be in the future"
        return v

    @model_validator(mode="after")
    def _reachable(self) -> "BookingCreateRequest":
        assert self.email or self.phone, "at least one of email or phone is required"
        return self


class BookingResponse(BaseModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    contact_id: uuid.UUID
    lead_id: Optional[uuid.UUID]
    booking_status: BookingStatus
    scheduled_for: datetime
    timezone: str
    service_address: dict
    notes: Optional[str]
    created_at: datetime
