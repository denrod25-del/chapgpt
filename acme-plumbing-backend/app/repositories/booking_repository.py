import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.contact import Contact
from app.models.event_log import EventLog


async def create(
    db: AsyncSession,
    *,
    brand_id: uuid.UUID,
    contact_id: uuid.UUID,
    lead_id: Optional[uuid.UUID],
    scheduled_for: datetime,
    timezone: str,
    service_address_json: dict,
    notes: Optional[str],
) -> Booking:
    booking = Booking(
        brand_id=brand_id,
        contact_id=contact_id,
        lead_id=lead_id,
        scheduled_for=scheduled_for,
        timezone=timezone,
        service_address_json=service_address_json,
        notes=notes,
    )
    db.add(booking)
    await db.flush()
    return booking


async def get_by_id(db: AsyncSession, booking_id: uuid.UUID) -> Optional[Booking]:
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    return result.scalar_one_or_none()


async def fetch_due_reminders(
    db: AsyncSession, *, window_start: datetime, window_end: datetime, limit: int = 100
) -> list[tuple[Booking, Contact]]:
    """Active bookings scheduled within [window_start, window_end] that have not
    yet had an 'appointment_reminder_sent' event logged. The NOT EXISTS guard is
    how we avoid re-reminding without a dedicated reminders table."""
    already_sent = exists().where(
        and_(
            EventLog.booking_id == Booking.id,
            EventLog.event_name == "appointment_reminder_sent",
        )
    )
    result = await db.execute(
        select(Booking, Contact)
        .join(Contact, Contact.id == Booking.contact_id)
        .where(
            Booking.booking_status.in_(("pending", "scheduled", "confirmed")),
            Booking.scheduled_for >= window_start,
            Booking.scheduled_for <= window_end,
            ~already_sent,
        )
        .order_by(Booking.scheduled_for.asc())
        .limit(limit)
    )
    return list(result.all())
