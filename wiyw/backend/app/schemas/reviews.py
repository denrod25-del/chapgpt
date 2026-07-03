"""Review capture + review-request schemas."""
from typing import Optional

from pydantic import BaseModel, Field

from .webhooks import CommChannel


class ReviewIn(BaseModel):
    customer_id: Optional[str] = None
    job_id: Optional[str] = None
    rating: int = Field(ge=1, le=5)
    platform: str = Field(pattern="^(google|facebook|internal)$")
    content: Optional[str] = Field(default=None, max_length=4000)


class ReviewRequestPayload(BaseModel):
    """POST /api/v1/reviews/request — trigger the split-leg review flow for a job."""
    job_id: str
    channel_override: Optional[CommChannel] = None  # default: SMS if consent, else email


class ReviewRequestOut(BaseModel):
    job_id: str
    scheduled: bool
    channel: CommChannel
    review_link: str
