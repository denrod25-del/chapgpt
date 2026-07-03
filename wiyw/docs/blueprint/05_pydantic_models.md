# SECTION 5 — Pydantic Models

Pydantic **v2** throughout. Existing models are shipped and boot-tested — reuse them; new
models below follow the same style (strict boundary validation, enums, E.164 asserts).

## Shipped (do not redefine)

| Model | File | Used by |
|---|---|---|
| `LeadIn`, `LeadOut`, `EventIn` + `ServiceType`/`Urgency`/`WaterSource` enums | `app/models/schemas.py` | `/leads`, `/events` |
| `BookingIn`, `BookingStatusUpdate`, `JobIn`, `JobComplete`, `QuoteIn`, `ReviewIn`, `BookingStatus` enum | `app/routers/schemas_ext.py` | `/bookings`, `/jobs`, `/quotes`, `/reviews` |

`LeadIn` **is** the lead-capture submission model; `QuoteIn` the quote request; `BookingIn` the
booking request. Field-by-field reference: read the two files — they're short and canonical.

## New models (add in `app/schemas/` at the v1 refactor)

```python
"""app/schemas/webhooks.py — inbound webhook + comm-log models."""
import re
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator

E164 = re.compile(r"^\+[1-9]\d{7,14}$")


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
    inbox_id: Optional[str] = None          # None when skipped as duplicate
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
```

```python
"""app/schemas/reviews.py — review request trigger payload."""
class ReviewRequestPayload(BaseModel):
    """POST /api/v1/reviews/request — trigger the split-leg review flow for a job."""
    job_id: str
    channel_override: Optional[CommChannel] = None  # default: SMS if consent, else email
    delay_hours: int = Field(default=2, ge=0, le=168)


class ReviewRequestOut(BaseModel):
    job_id: str
    scheduled: bool
    channel: CommChannel
    review_link: str
```

```python
"""app/schemas/integrations.py — provider-facing payloads."""
class BrevoContactSync(BaseModel):
    """POST /api/v1/integrations/brevo/sync-contact.
    Mirrors a Postgres contact into Brevo. Attribute names are the canonical
    UPPER_SNAKE set from docs/BREVO_SETUP.md."""
    email: Optional[str] = Field(default=None, max_length=320)
    phone: str                                    # E.164; Brevo 'sms' field
    list_ids: list[int] = Field(default_factory=lambda: [2])  # 2 = list_leads
    attributes: dict[str, str | int | float | bool] = Field(default_factory=dict)
    update_enabled: bool = True

    @field_validator("phone")
    @classmethod
    def _e164(cls, v: str) -> str:
        v = v.strip()
        assert E164.match(v), "phone must be E.164"
        return v

    @field_validator("attributes")
    @classmethod
    def _upper_snake(cls, v: dict) -> dict:
        assert all(re.match(r"^[A-Z][A-Z0-9_]*$", k) for k in v), \
            "Brevo attribute names must be UPPER_SNAKE"
        return v


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
    """POST /api/v1/integrations/{resend|mailgun}/send-email (internal-auth only)."""
    to: str = Field(max_length=320)
    subject: str = Field(min_length=1, max_length=200)
    html: str = Field(min_length=1)
    template: str = Field(min_length=1, max_length=100)  # txn_* key
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None
```

Notes:
- **Required vs optional is explicit**: no field is optional unless the DB column is nullable.
- Enums everywhere a CHECK constraint exists — the API surface and the schema can't drift.
- `EventIn` (shipped) is the event-creation model; event names are validated by the DB CHECK,
  which is deliberate: one place (migration 005) defines the taxonomy. If you want 422 instead
  of 500 on bad names, mirror the taxonomy into a `str Enum` and keep it in sync with 005.
