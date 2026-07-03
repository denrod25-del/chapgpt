"""Provider-facing payloads for the internal /integrations/* routes."""
import re
from typing import Optional, Union

from pydantic import BaseModel, Field, field_validator

E164 = re.compile(r"^\+[1-9]\d{7,14}$")
UPPER_SNAKE = re.compile(r"^[A-Z][A-Z0-9_]*$")


class BrevoContactSync(BaseModel):
    """POST /api/v1/integrations/brevo/sync-contact.
    Mirrors a Postgres contact into Brevo. Attribute names are the canonical
    UPPER_SNAKE set from docs/BREVO_SETUP.md."""
    email: Optional[str] = Field(default=None, max_length=320)
    phone: str                                    # E.164; Brevo 'sms' field
    list_ids: Optional[list[int]] = None          # default: config.BREVO_LIST_NEW_LEADS
    attributes: dict[str, Union[str, int, float, bool]] = Field(default_factory=dict)
    update_enabled: bool = True
    lead_id: Optional[str] = None                 # store returned contact id on this lead

    @field_validator("phone")
    @classmethod
    def _e164(cls, v: str) -> str:
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


class SmsSend(BaseModel):
    """POST /api/v1/integrations/gatewayapi/send-sms (internal-auth only)."""
    to: str                                       # E.164
    message: str = Field(min_length=1, max_length=459)   # 3 concatenated GSM-7 segments max
    template: str = Field(min_length=1, max_length=100)  # sms_* key, for the comm log
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None

    @field_validator("to")
    @classmethod
    def _e164(cls, v: str) -> str:
        v = v.strip()
        assert E164.match(v), "to must be E.164"
        return v


class SmsSendOut(BaseModel):
    sent: bool
    provider_msg_id: Optional[str] = None


class EmailSend(BaseModel):
    """POST /api/v1/integrations/resend/send-email (internal-auth only).
    Resend primary; Mailgun failover happens inside the email service."""
    to: str = Field(max_length=320)
    subject: str = Field(min_length=1, max_length=200)
    html: str = Field(min_length=1)
    template: str = Field(min_length=1, max_length=100)  # txn_* key
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None


class EmailSendOut(BaseModel):
    sent: bool
    provider: Optional[str] = None                # 'resend' | 'mailgun' | None
