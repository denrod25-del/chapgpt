"""Review-request scheduling + lifecycle transitions.

create → (n8n polls) fetch_due → mark_sent → [webhook: delivered/clicked] →
mark_completed (or mark_failed). Each transition writes a canonical event_log row.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.contact import Contact
from app.models.review_request import ReviewRequest
from app.repositories import event_repository, get_brand_id_by_slug
from app.repositories import review_request_repository as rr_repo
from app.schemas.provider_events import EventName
from app.schemas.review_request import (
    DueReviewRequest,
    MarkCompletedRequest,
    MarkFailedRequest,
    MarkSentRequest,
    ReviewRequestActionOut,
    ReviewRequestCreate,
    ReviewRequestOut,
)


def _to_out(row: ReviewRequest) -> ReviewRequestOut:
    return ReviewRequestOut(
        id=row.id, brand_id=row.brand_id, contact_id=row.contact_id,
        lead_id=row.lead_id, booking_id=row.booking_id,
        communication_log_id=row.communication_log_id, channel=row.channel,
        status=row.status, review_url=row.review_url, scheduled_for=row.scheduled_for,
        sent_at=row.sent_at, completed_at=row.completed_at,
        failure_reason=row.failure_reason, created_at=row.created_at,
    )


async def _load(db: AsyncSession, rr_id: uuid.UUID) -> ReviewRequest:
    row = await rr_repo.get_by_id(db, rr_id)
    if row is None:
        raise HTTPException(404, "review request not found")
    return row


async def create_review_request(
    db: AsyncSession, payload: ReviewRequestCreate
) -> ReviewRequestOut:
    brand_id = await get_brand_id_by_slug(db, payload.brand_slug)
    if brand_id is None:
        raise HTTPException(422, f"unknown brand_slug '{payload.brand_slug}'")

    contact = (await db.execute(
        select(Contact).where(Contact.id == payload.contact_id)
    )).scalar_one_or_none()
    if contact is None or contact.brand_id != brand_id:
        raise HTTPException(422, "contact_id does not belong to this brand")

    delay = payload.delay_minutes
    if delay is None:
        delay = settings.REVIEW_REQUEST_DEFAULT_DELAY_MINUTES
    scheduled_for = payload.scheduled_for or (
        datetime.now(timezone.utc) + timedelta(minutes=delay)
    )
    review_url = payload.review_url or settings.DEFAULT_REVIEW_URL

    row = await rr_repo.create(
        db, brand_id=brand_id, contact_id=payload.contact_id,
        lead_id=payload.lead_id, booking_id=payload.booking_id,
        channel=payload.channel, review_url=review_url,
        scheduled_for=scheduled_for, metadata_json=payload.metadata,
    )
    await event_repository.create(
        db, brand_id=brand_id, event_name=EventName.review_request_scheduled,
        event_source="backend", contact_id=payload.contact_id,
        lead_id=payload.lead_id, booking_id=payload.booking_id,
        payload_json={"review_request_id": str(row.id), "channel": payload.channel,
                      "scheduled_for": scheduled_for.isoformat()},
    )
    await db.commit()
    return _to_out(row)


async def fetch_due_review_requests(
    db: AsyncSession, *, limit: int = 100
) -> list[DueReviewRequest]:
    """Flip pending→due, then return everything ready to dispatch with contact
    context. Marking due first makes the poll idempotent and observable."""
    await rr_repo.mark_due(db)
    rows = await rr_repo.fetch_due(db, limit=limit)
    await db.commit()
    return [
        DueReviewRequest(
            id=rr.id, brand_id=rr.brand_id, contact_id=rr.contact_id,
            channel=rr.channel, review_url=rr.review_url,
            scheduled_for=rr.scheduled_for, first_name=contact.first_name,
            email=contact.email, phone=contact.phone,
        )
        for rr, contact in rows
    ]


async def mark_review_request_sent(
    db: AsyncSession, rr_id: uuid.UUID, payload: MarkSentRequest
) -> ReviewRequestActionOut:
    row = await _load(db, rr_id)
    row.status = "sent"
    row.sent_at = datetime.now(timezone.utc)
    if payload.communication_log_id is not None:
        row.communication_log_id = payload.communication_log_id
    if payload.external_message_id:
        meta = dict(row.metadata_json or {})
        meta["external_message_id"] = payload.external_message_id
        if payload.provider:
            meta["provider"] = payload.provider
        row.metadata_json = meta
    await event_repository.create(
        db, brand_id=row.brand_id, event_name=EventName.review_request_sent,
        event_source="n8n", contact_id=row.contact_id, lead_id=row.lead_id,
        booking_id=row.booking_id,
        payload_json={"review_request_id": str(row.id),
                      "external_message_id": payload.external_message_id},
    )
    await db.commit()
    return ReviewRequestActionOut(id=row.id, status=row.status)


async def mark_review_request_failed(
    db: AsyncSession, rr_id: uuid.UUID, payload: MarkFailedRequest
) -> ReviewRequestActionOut:
    row = await _load(db, rr_id)
    row.status = "failed"
    row.failure_reason = payload.failure_reason
    await event_repository.create(
        db, brand_id=row.brand_id, event_name=EventName.review_request_failed,
        event_source="n8n", contact_id=row.contact_id, lead_id=row.lead_id,
        booking_id=row.booking_id,
        payload_json={"review_request_id": str(row.id),
                      "failure_reason": payload.failure_reason},
    )
    await db.commit()
    return ReviewRequestActionOut(id=row.id, status=row.status)


async def mark_review_request_completed(
    db: AsyncSession, rr_id: uuid.UUID, payload: MarkCompletedRequest
) -> ReviewRequestActionOut:
    row = await _load(db, rr_id)
    row.status = "completed"
    row.completed_at = payload.completed_at or datetime.now(timezone.utc)
    if payload.metadata:
        row.metadata_json = {**(row.metadata_json or {}), **payload.metadata}
    await event_repository.create(
        db, brand_id=row.brand_id, event_name=EventName.review_request_completed,
        event_source="n8n", contact_id=row.contact_id, lead_id=row.lead_id,
        booking_id=row.booking_id,
        payload_json={"review_request_id": str(row.id)},
    )
    await db.commit()
    return ReviewRequestActionOut(id=row.id, status=row.status)
