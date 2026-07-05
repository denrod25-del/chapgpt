"""n8n lifecycle automation: due appointment reminders + relayed delivery posts.

Appointment reminders have no dedicated table — "already reminded" is derived
from an `appointment_reminder_sent` event_log row. After sending, n8n posts that
event back via POST /api/v1/events (booking_id set), which removes the booking
from the next due poll.
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories import booking_repository, communication_repository, event_repository
from app.schemas.automation import DeliveryUpdateOut, DeliveryUpdateRequest, DueAppointmentReminder
from app.schemas.provider_events import map_provider_event


async def fetch_due_appointment_reminders(
    db: AsyncSession, *, limit: int = 100
) -> list[DueAppointmentReminder]:
    now = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=settings.APPOINTMENT_REMINDER_LEAD_HOURS)
    rows = await booking_repository.fetch_due_reminders(
        db, window_start=now, window_end=window_end, limit=limit
    )
    return [
        DueAppointmentReminder(
            booking_id=b.id, brand_id=b.brand_id, contact_id=b.contact_id,
            scheduled_for=b.scheduled_for, timezone=b.timezone,
            first_name=contact.first_name, email=contact.email, phone=contact.phone,
            service_address=b.service_address_json or {},
        )
        for b, contact in rows
    ]


async def post_delivery_update(
    db: AsyncSession, communication_log_id: uuid.UUID, payload: DeliveryUpdateRequest
) -> DeliveryUpdateOut:
    """Apply a relayed delivery outcome to a specific communication_logs row.
    The provider-native `status` is mapped canonically, applied forward-only, and
    an event_log row is written."""
    row = await communication_repository.get_by_id(db, communication_log_id)
    if row is None:
        raise HTTPException(404, "communication_log not found")

    canonical_event, delivery_status, _flags = map_provider_event(
        payload.provider, payload.status
    )
    updated = await communication_repository.apply_delivery_update(
        row, new_status=delivery_status, occurred_at=payload.occurred_at
    )
    await event_repository.create(
        db, brand_id=row.brand_id, event_name=canonical_event,
        event_source=payload.provider, contact_id=row.contact_id,
        lead_id=row.lead_id, booking_id=row.booking_id,
        payload_json={"communication_log_id": str(row.id),
                      "provider_status": payload.status, **payload.metadata},
        occurred_at=payload.occurred_at,
    )
    await db.commit()
    return DeliveryUpdateOut(
        communication_log_id=row.id, delivery_status=row.delivery_status,
        event_name=canonical_event, updated=updated,
    )
