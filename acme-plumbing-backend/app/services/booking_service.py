"""Booking request flow: resolve brand → upsert contact → create booking → log event."""
import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.booking import Booking
from app.repositories import (
    booking_repository,
    event_repository,
    get_brand_id_by_slug,
    get_or_create_contact,
)
from app.schemas.booking import BookingCreateRequest, BookingResponse
from app.schemas.common import BookingStatus


def _to_response(booking: Booking) -> BookingResponse:
    return BookingResponse(
        id=booking.id,
        brand_id=booking.brand_id,
        contact_id=booking.contact_id,
        lead_id=booking.lead_id,
        booking_status=BookingStatus(booking.booking_status),
        scheduled_for=booking.scheduled_for,
        timezone=booking.timezone,
        service_address=booking.service_address_json,
        notes=booking.notes,
        created_at=booking.created_at,
    )


async def create_booking(db: AsyncSession, payload: BookingCreateRequest) -> BookingResponse:
    brand_id = await get_brand_id_by_slug(db, payload.brand_slug)
    if brand_id is None:
        raise HTTPException(422, f"unknown brand_slug '{payload.brand_slug}'")

    contact = await get_or_create_contact(
        db, brand_id=brand_id, first_name=payload.first_name,
        last_name=payload.last_name, email=payload.email, phone=payload.phone,
        source="booking_form",
    )
    booking = await booking_repository.create(
        db, brand_id=brand_id, contact_id=contact.id, lead_id=payload.lead_id,
        scheduled_for=payload.scheduled_for,
        timezone=payload.timezone or settings.DEFAULT_TIMEZONE,
        service_address_json=payload.service_address, notes=payload.notes,
    )
    await event_repository.create(
        db, brand_id=brand_id, event_name="booking_requested", event_source="backend",
        contact_id=contact.id, lead_id=payload.lead_id, booking_id=booking.id,
        payload_json={"scheduled_for": payload.scheduled_for.isoformat()},
    )
    await db.commit()

    # TODO: confirmation SMS/email as background work once providers are wired.
    return _to_response(booking)


async def get_booking(db: AsyncSession, booking_id: uuid.UUID) -> BookingResponse:
    booking: Optional[Booking] = await booking_repository.get_by_id(db, booking_id)
    if booking is None:
        raise HTTPException(404, "booking not found")
    return _to_response(booking)
