"""Repository layer — all DB operations live under this package.

This module holds the two cross-entity lookups shared by every service
(brand resolution + contact upsert); entity-specific operations live in
their own *_repository modules.
"""
import uuid
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand import Brand
from app.models.contact import Contact


async def get_brand_id_by_slug(db: AsyncSession, slug: str) -> Optional[uuid.UUID]:
    result = await db.execute(
        select(Brand.id).where(Brand.slug == slug, Brand.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def single_active_brand_id(db: AsyncSession) -> Optional[uuid.UUID]:
    """Return the only active brand's id, or None if zero or more than one.
    Reconciliation uses this to attribute a provider event that has no local
    communication_logs match — safe only while the deployment is single-brand."""
    result = await db.execute(select(Brand.id).where(Brand.is_active.is_(True)).limit(2))
    ids = result.scalars().all()
    return ids[0] if len(ids) == 1 else None


async def find_contact(
    db: AsyncSession,
    *,
    brand_id: uuid.UUID,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> Optional[Contact]:
    """Locate a contact within a brand by email (case-insensitive) or phone.
    Used to flag unsubscribe/complaint/bounce signals from provider webhooks."""
    if email:
        result = await db.execute(
            select(Contact).where(
                Contact.brand_id == brand_id,
                func.lower(Contact.email) == email.lower(),
            )
        )
        contact = result.scalar_one_or_none()
        if contact is not None:
            return contact
    if phone:
        result = await db.execute(
            select(Contact).where(Contact.brand_id == brand_id, Contact.phone == phone)
        )
        return result.scalar_one_or_none()
    return None


def add_contact_tags(contact: Contact, *tags: str) -> bool:
    """Add tags to a contact's tags_json without duplicates. Reassigns the list
    so SQLAlchemy detects the mutation (JSONB in-place edits aren't tracked).
    Returns True if anything changed. Caller owns commit."""
    current = list(contact.tags_json or [])
    changed = False
    for tag in tags:
        if tag not in current:
            current.append(tag)
            changed = True
    if changed:
        contact.tags_json = current
    return changed


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
    Fills in missing email/phone on an existing contact; never overwrites.

    Email match is case-insensitive to mirror the uq_contacts_brand_email
    partial unique index on lower(email) — an exact-match lookup would miss
    rows written with different casing and then trip the index on insert."""
    contact: Optional[Contact] = None
    if email:
        result = await db.execute(
            select(Contact).where(
                Contact.brand_id == brand_id,
                func.lower(Contact.email) == email.lower(),
            )
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
