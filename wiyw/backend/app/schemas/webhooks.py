"""Webhook + communication-log schemas."""
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class WebhookProvider(str, Enum):
    brevo = "brevo"
    mailgun = "mailgun"
    resend = "resend"
    gatewayapi = "gatewayapi"
    storyblok = "storyblok"
    forms = "forms"
    internal = "internal"
    other = "other"


class WebhookReceipt(BaseModel):
    """Response returned by every webhook endpoint: fast ack, inbox row id."""
    ok: bool = True
    inbox_id: Optional[str] = None      # None when skipped as duplicate
    duplicate: bool = False


class CommChannel(str, Enum):
    email = "email"
    sms = "sms"


class CommDirection(str, Enum):
    outbound = "outbound"
    inbound = "inbound"


class CommProvider(str, Enum):
    resend = "resend"
    mailgun = "mailgun"
    gatewayapi = "gatewayapi"
    brevo = "brevo"


class CommLogCreate(BaseModel):
    """Internal creation payload for communication_logs (used by services + n8n)."""
    channel: CommChannel
    direction: CommDirection = CommDirection.outbound
    to_addr: str = Field(min_length=3, max_length=320)
    provider: CommProvider
    template: str = Field(min_length=1, max_length=100)   # e.g. 'sms_reminder_24h'
    status: str = Field(default="sent", max_length=50)
    provider_msg_id: Optional[str] = None
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None
