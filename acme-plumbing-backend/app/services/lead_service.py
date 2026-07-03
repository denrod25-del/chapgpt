"""Lead intake flow: resolve brand → upsert contact → create lead → log event."""
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import (
    event_repository,
    get_brand_id_by_slug,
    get_or_create_contact,
    lead_repository,
)
from app.schemas.common import LeadStatus
from app.schemas.lead import LeadCreateRequest, LeadCreateResponse


async def create_lead(db: AsyncSession, payload: LeadCreateRequest) -> LeadCreateResponse:
    # Idempotent replay: same key returns the original lead, no side effects.
    if payload.idempotency_key:
        existing = await lead_repository.get_by_idempotency_key(db, payload.idempotency_key)
        if existing is not None:
            return LeadCreateResponse(
                id=existing.id, status=LeadStatus(existing.status),
                contact_id=existing.contact_id,
            )

    brand_id = await get_brand_id_by_slug(db, payload.brand_slug)
    if brand_id is None:
        raise HTTPException(422, f"unknown brand_slug '{payload.brand_slug}'")

    contact = await get_or_create_contact(
        db, brand_id=brand_id, first_name=payload.first_name,
        last_name=payload.last_name, email=payload.email, phone=payload.phone,
        source=payload.source,
    )
    lead = await lead_repository.create(
        db, brand_id=brand_id, contact_id=contact.id,
        lead_type=payload.lead_type.value, source=payload.source,
        service_type=payload.service_type, urgency=payload.urgency.value,
        message=payload.message, page_url=payload.page_url,
        utm_json=payload.utm, meta_json=payload.meta,
        idempotency_key=payload.idempotency_key,
    )
    await event_repository.create(
        db, brand_id=brand_id, event_name="lead_created", event_source="backend",
        contact_id=contact.id, lead_id=lead.id,
        payload_json={"lead_type": payload.lead_type.value,
                      "source": payload.source, "urgency": payload.urgency.value},
    )

    try:
        await db.commit()
    except IntegrityError:
        # Lost an idempotency race: another request committed the same key first.
        await db.rollback()
        assert payload.idempotency_key is not None
        existing = await lead_repository.get_by_idempotency_key(db, payload.idempotency_key)
        assert existing is not None, "idempotency conflict without a stored lead"
        return LeadCreateResponse(
            id=existing.id, status=LeadStatus(existing.status),
            contact_id=existing.contact_id,
        )

    # TODO: enqueue post-create side effects (Brevo contact sync via
    # integrations.brevo_client, confirmation SMS via integrations.gatewayapi_client)
    # as background work; log each send to communication_logs.
    return LeadCreateResponse(
        id=lead.id, status=LeadStatus(lead.status), contact_id=contact.id
    )
