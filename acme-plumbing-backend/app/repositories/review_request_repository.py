import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.contact import Contact
from app.models.review_request import ReviewRequest

# Bookings in these states should never trigger a review ask.
_DEAD_BOOKING_STATES = ("cancelled", "no_show")


async def create(
    db: AsyncSession,
    *,
    brand_id: uuid.UUID,
    contact_id: uuid.UUID,
    lead_id: Optional[uuid.UUID],
    booking_id: Optional[uuid.UUID],
    channel: str,
    review_url: str,
    scheduled_for: datetime,
    metadata_json: dict,
) -> ReviewRequest:
    row = ReviewRequest(
        brand_id=brand_id,
        contact_id=contact_id,
        lead_id=lead_id,
        booking_id=booking_id,
        channel=channel,
        review_url=review_url,
        scheduled_for=scheduled_for,
        metadata_json=metadata_json,
    )
    db.add(row)
    await db.flush()
    return row


async def get_by_id(db: AsyncSession, rr_id: uuid.UUID) -> Optional[ReviewRequest]:
    result = await db.execute(
        select(ReviewRequest).where(ReviewRequest.id == rr_id)
    )
    return result.scalar_one_or_none()


async def mark_due(db: AsyncSession, *, now: Optional[datetime] = None) -> int:
    """Flip pending → due for everything whose scheduled_for has passed.
    Returns the number of rows transitioned. Caller owns commit."""
    now = now or datetime.now(timezone.utc)
    result = await db.execute(
        update(ReviewRequest)
        .where(ReviewRequest.status == "pending", ReviewRequest.scheduled_for <= now)
        .values(status="due")
    )
    return result.rowcount or 0


async def fetch_due(
    db: AsyncSession, *, limit: int = 100, now: Optional[datetime] = None
) -> list[tuple[ReviewRequest, Contact]]:
    """Rows ready to dispatch (pending/due and past schedule), joined to their
    contact so the caller can build an SMS/email without a second query.

    Requests linked to a cancelled / no-show booking are skipped: 03 schedules
    the review at booking time, so a booking that fell through must not still
    generate a review ask. Requests with no booking (booking_id NULL) are
    unaffected."""
    now = now or datetime.now(timezone.utc)
    dead_booking = exists().where(
        and_(
            Booking.id == ReviewRequest.booking_id,
            Booking.booking_status.in_(_DEAD_BOOKING_STATES),
        )
    )
    result = await db.execute(
        select(ReviewRequest, Contact)
        .join(Contact, Contact.id == ReviewRequest.contact_id)
        .where(
            ReviewRequest.status.in_(("pending", "due")),
            ReviewRequest.scheduled_for <= now,
            ~dead_booking,
        )
        .order_by(ReviewRequest.scheduled_for.asc())
        .limit(limit)
    )
    return list(result.all())
