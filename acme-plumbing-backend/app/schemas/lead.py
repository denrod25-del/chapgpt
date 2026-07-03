import re
import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.schemas.common import LeadStatus, LeadType, Urgency

E164 = re.compile(r"^\+[1-9]\d{7,14}$")


class LeadCreateRequest(BaseModel):
    brand_slug: str = Field(default="acme-plumbing", min_length=1, max_length=100)
    lead_type: LeadType = LeadType.website_form
    first_name: str = Field(min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None                      # E.164
    service_type: Optional[str] = Field(default=None, max_length=50)
    urgency: Urgency = Urgency.standard
    message: Optional[str] = Field(default=None, max_length=2000)
    source: str = Field(default="website", min_length=1, max_length=100)
    page_url: Optional[str] = Field(default=None, max_length=500)
    utm: dict[str, str] = Field(default_factory=dict)
    meta: dict = Field(default_factory=dict)
    idempotency_key: Optional[str] = Field(default=None, max_length=200)

    @field_validator("phone")
    @classmethod
    def _phone_e164(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        assert E164.match(v), "phone must be E.164 (e.g. +15615550123)"
        return v

    @model_validator(mode="after")
    def _reachable(self) -> "LeadCreateRequest":
        assert self.email or self.phone, "at least one of email or phone is required"
        return self


class LeadCreateResponse(BaseModel):
    id: uuid.UUID
    status: LeadStatus
    contact_id: Optional[uuid.UUID]
