"""Review-request payload (n8n workflow 05). Acme has no jobs table yet, so
job_id is an opaque reference; the endpoint records the request + returns a link."""

from pydantic import BaseModel, Field


class ReviewRequestPayload(BaseModel):
    brand_slug: str = Field(default="acme-plumbing", min_length=1, max_length=100)
    job_id: str = Field(min_length=1, max_length=100)
    channel: str = Field(default="sms", pattern="^(sms|email)$")


class ReviewRequestOut(BaseModel):
    job_id: str
    scheduled: bool
    channel: str
    review_link: str
