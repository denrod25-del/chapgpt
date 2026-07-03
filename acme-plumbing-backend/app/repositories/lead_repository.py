import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead


async def create(
    db: AsyncSession,
    *,
    brand_id: uuid.UUID,
    contact_id: Optional[uuid.UUID],
    lead_type: str,
    source: str,
    service_type: Optional[str],
    urgency: str,
    message: Optional[str],
    page_url: Optional[str],
    utm_json: dict,
    meta_json: dict,
    idempotency_key: Optional[str],
) -> Lead:
    lead = Lead(
        brand_id=brand_id,
        contact_id=contact_id,
        lead_type=lead_type,
        source=source,
        service_type=service_type,
        urgency=urgency,
        message=message,
        page_url=page_url,
        utm_json=utm_json,
        meta_json=meta_json,
        idempotency_key=idempotency_key,
    )
    db.add(lead)
    await db.flush()
    return lead


async def get_by_idempotency_key(db: AsyncSession, key: str) -> Optional[Lead]:
    result = await db.execute(select(Lead).where(Lead.idempotency_key == key))
    return result.scalar_one_or_none()
