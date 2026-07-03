import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event_log import EventLog


async def create(
    db: AsyncSession,
    *,
    brand_id: uuid.UUID,
    event_name: str,
    event_source: str,
    contact_id: Optional[uuid.UUID] = None,
    lead_id: Optional[uuid.UUID] = None,
    booking_id: Optional[uuid.UUID] = None,
    payload_json: Optional[dict] = None,
    occurred_at: Optional[datetime] = None,
) -> EventLog:
    event = EventLog(
        brand_id=brand_id,
        event_name=event_name,
        event_source=event_source,
        contact_id=contact_id,
        lead_id=lead_id,
        booking_id=booking_id,
        payload_json=payload_json or {},
    )
    if occurred_at is not None:
        event.occurred_at = occurred_at
    db.add(event)
    await db.flush()
    return event
