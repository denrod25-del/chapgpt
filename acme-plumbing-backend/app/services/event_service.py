"""Event ingestion flow."""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import event_repository, get_brand_id_by_slug
from app.schemas.event import EventCreateRequest, EventResponse


async def record_event(db: AsyncSession, payload: EventCreateRequest) -> EventResponse:
    brand_id = await get_brand_id_by_slug(db, payload.brand_slug)
    if brand_id is None:
        raise HTTPException(422, f"unknown brand_slug '{payload.brand_slug}'")

    event = await event_repository.create(
        db, brand_id=brand_id, event_name=payload.event_name,
        event_source=payload.event_source, contact_id=payload.contact_id,
        lead_id=payload.lead_id, booking_id=payload.booking_id,
        payload_json=payload.payload, occurred_at=payload.occurred_at,
    )
    await db.commit()
    return EventResponse(id=event.id, event_name=event.event_name,
                         occurred_at=event.occurred_at)
