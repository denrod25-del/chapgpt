"""Reconcile a canonical NormalizedEvent into local state.

Responsibilities (all within the caller's transaction — no commit here):
  1. Map the provider message id back to a communication_logs row.
  2. Advance that row's delivery_status (forward-only, negatives always win).
  3. Flag the contact on unsubscribe / complaint / bounce.
  4. Append an event_log row for the lifecycle change.

Unknown provider message ids are handled safely: we still try to attribute the
event to the single active brand and log it; if the brand can't be resolved we
return matched=False and skip the event rather than raise.
"""
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.repositories import (
    add_contact_tags,
    event_repository,
    find_contact,
    single_active_brand_id,
)
from app.repositories import communication_repository
from app.schemas.provider_events import NormalizedEvent

_BOUNCE_TAG = "email_bounced"
_COMPLAINT_TAG = "complained"
_UNSUB_TAG = "unsubscribed"


@dataclass
class ReconcileResult:
    matched: bool = False            # a communication_logs row was found
    delivery_updated: bool = False   # delivery_status advanced
    contact_flagged: bool = False
    event_logged: bool = False
    event_name: Optional[str] = None


async def _load_contact(
    db: AsyncSession, comm_log, brand_id, normalized: NormalizedEvent
) -> Optional[Contact]:
    if comm_log is not None and comm_log.contact_id is not None:
        result = await db.execute(
            select(Contact).where(Contact.id == comm_log.contact_id)
        )
        contact = result.scalar_one_or_none()
        if contact is not None:
            return contact
    if brand_id is not None:
        return await find_contact(
            db, brand_id=brand_id, email=normalized.email, phone=normalized.phone
        )
    return None


async def reconcile(db: AsyncSession, normalized: NormalizedEvent) -> ReconcileResult:
    result = ReconcileResult(event_name=normalized.canonical_event)

    comm_log = None
    if normalized.external_message_id:
        comm_log = await communication_repository.get_by_external_id(
            db, normalized.provider, normalized.external_message_id
        )
    result.matched = comm_log is not None

    brand_id = comm_log.brand_id if comm_log is not None else await single_active_brand_id(db)

    # 1. delivery_status advance (only against a known row).
    if comm_log is not None:
        result.delivery_updated = await communication_repository.apply_delivery_update(
            comm_log,
            new_status=normalized.delivery_status,
            occurred_at=normalized.occurred_at,
        )

    # 2. contact flags for negative signals.
    if normalized.is_bounce or normalized.is_complaint or normalized.is_unsubscribe:
        contact = await _load_contact(db, comm_log, brand_id, normalized)
        if contact is not None:
            tags = []
            if normalized.is_bounce:
                tags.append(_BOUNCE_TAG)
            if normalized.is_complaint:
                tags.append(_COMPLAINT_TAG)
            if normalized.is_unsubscribe:
                tags.append(_UNSUB_TAG)
            result.contact_flagged = add_contact_tags(contact, *tags)

    # 3. lifecycle event (needs a brand; unmatched multi-brand events are skipped).
    if brand_id is not None:
        await event_repository.create(
            db,
            brand_id=brand_id,
            event_name=normalized.canonical_event,
            event_source=normalized.provider,
            contact_id=comm_log.contact_id if comm_log is not None else None,
            lead_id=comm_log.lead_id if comm_log is not None else None,
            booking_id=comm_log.booking_id if comm_log is not None else None,
            payload_json={
                "provider_event": normalized.provider_event,
                "external_message_id": normalized.external_message_id,
                "email": normalized.email,
                "phone": normalized.phone,
                "tags": normalized.tags,
                "matched": result.matched,
            },
            occurred_at=normalized.occurred_at,
        )
        result.event_logged = True

    return result
