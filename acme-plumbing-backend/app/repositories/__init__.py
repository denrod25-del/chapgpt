"""Repository layer — all DB operations live under this package.

This module holds the two cross-entity lookups shared by every service
(brand resolution + contact upsert); entity-specific operations live in
their own *_repository modules.
"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand import Brand
from app.models.contact import Contact


async def get_brand_id_by_slug(db: AsyncSession, slug: str) -> Optional[uuid.UUID]:
    result = await db.execute(
        select(Brand.id).where(Brand.slug == slug, Brand.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def get_or_create_contact(
    db: AsyncSession,
    *,
    brand_id: uuid.UUID,
    first_name: str,
    last_name: Optional[str],
    email: Optional[str],
    phone: Optional[str],
    source: str,
) -> Contact:
    """Upsert identity: (brand, email) first, then (brand, phone).
    Fills in missing email/phone on an existing contact; never overwrites."""
    contact: Optional[Contact] = None
    if email:
        result = await db.execute(
            select(Contact).where(Contact.brand_id == brand_id, Contact.email == email.lower())
        )
        contact = result.scalar_one_or_none()
    if contact is None and phone:
        result = await db.execute(
            select(Contact).where(Contact.brand_id == brand_id, Contact.phone == phone)
        )
        contact = result.scalar_one_or_none()

    if contact is not None:
        if email and not contact.email:
            contact.email = email.lower()
        if phone and not contact.phone:
            contact.phone = phone
        return contact

    contact = Contact(
        brand_id=brand_id,
        first_name=first_name,
        last_name=last_name,
        email=email.lower() if email else None,
        phone=phone,
        source=source,
    )
    db.add(contact)
    await db.flush()        # populates server-generated id
    return contact
