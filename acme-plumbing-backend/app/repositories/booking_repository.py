import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking


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
