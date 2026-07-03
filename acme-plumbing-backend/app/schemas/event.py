import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EventCreateRequest(BaseModel):
    brand_slug: str = Field(default="acme-plumbing", min_length=1, max_length=100)
    event_name: str = Field(min_length=1, max_length=100)    # snake_case, past tense
    event_source: str = Field(default="frontend", min_length=1, max_length=50)
    contact_id: Optional[uuid.UUID] = None
    lead_id: Optional[uuid.UUID] = None
    booking_id: Optional[uuid.UUID] = None
    payload: dict = Field(default_factory=dict)
    occurred_at: Optional[datetime] = None                   # default: now() in DB


class EventResponse(BaseModel):
    id: uuid.UUID
    event_name: str
    occurred_at: datetime
