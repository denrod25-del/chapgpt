"""Payloads for the internal /integrations/* routes (called by n8n)."""
import re
from typing import Optional, Union

from pydantic import BaseModel, EmailStr, Field, field_validator

E164 = re.compile(r"^\+[1-9]\d{7,14}$")
UPPER_SNAKE = re.compile(r"^[A-Z][A-Z0-9_]*$")


class SmsSend(BaseModel):
    brand_slug: str = Field(default="acme-plumbing", min_length=1, max_length=100)
    to: str                                              # E.164
    message: str = Field(min_length=1, max_length=800)
    template: str = Field(default="sms_generic", min_length=1, max_length=100)
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None                    # contact id (provenance only)

    @field_validator("to")
    @classmethod
    def _e164(cls, v: str) -> str:
        v = v.strip()
        assert E164.match(v), "to must be E.164 (e.g. +15615550123)"
        return v


class SmsSendOut(BaseModel):
    sent: bool
    provider_msg_id: Optional[str] = None


class EmailSend(BaseModel):
    brand_slug: str = Field(default="acme-plumbing", min_length=1, max_length=100)
    to: EmailStr
    subject: str = Field(min_length=1, max_length=200)
    html: str = Field(min_length=1)
    template: str = Field(default="txn_generic", min_length=1, max_length=100)
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None


class EmailSendOut(BaseModel):
    sent: bool
    provider: str = "resend"
    provider_msg_id: Optional[str] = None


class BrevoContactSync(BaseModel):
    brand_slug: str = Field(default="acme-plumbing", min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    lead_id: Optional[str] = None
    list_ids: Optional[list[int]] = None
    attributes: dict[str, Union[str, int, float, bool]] = Field(default_factory=dict)

    @field_validator("phone")
    @classmethod
    def _e164(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        assert E164.match(v), "phone must be E.164"
        return v

    @field_validator("attributes")
    @classmethod
    def _upper_snake(cls, v: dict) -> dict:
        assert all(UPPER_SNAKE.match(k) for k in v), \
            "Brevo attribute names must be UPPER_SNAKE"
        return v


class BrevoContactSyncOut(BaseModel):
    synced: bool
    contact_id: Optional[str] = None
