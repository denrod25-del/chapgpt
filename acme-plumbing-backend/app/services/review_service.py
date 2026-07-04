"""Review-request flow (n8n workflow 05). Records the request as an event +
communication_logs row and returns a review link. Acme has no jobs/reviews
tables yet, so job_id is opaque; wire the real gating in when those land."""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand import Brand
from app.repositories import comm_repository, event_repository
from app.schemas.review import ReviewRequestOut, ReviewRequestPayload


async def request_review(db: AsyncSession, payload: ReviewRequestPayload) -> ReviewRequestOut:
    brand = (await db.execute(
        Brand.__table__.select().where(Brand.slug == payload.brand_slug)
    )).mappings().first()
    if brand is None:
        raise HTTPException(422, f"unknown brand_slug '{payload.brand_slug}'")

    domain = brand["website_domain"] or "example.com"
    review_link = f"https://{domain}/review?job={payload.job_id}"

    await comm_repository.create(
        db, brand_id=brand["id"], channel=payload.channel, provider="gatewayapi",
        template_key="review_request", delivery_status="queued",
        body_preview=f"Review request for job {payload.job_id}",
        metadata_json={"job_id": payload.job_id, "review_link": review_link},
    )
    await event_repository.create(
        db, brand_id=brand["id"], event_name="review_request_sent", event_source="n8n",
        payload_json={"job_id": payload.job_id, "channel": payload.channel},
    )
    await db.commit()
    return ReviewRequestOut(
        job_id=payload.job_id, scheduled=True,
        channel=payload.channel, review_link=review_link)
