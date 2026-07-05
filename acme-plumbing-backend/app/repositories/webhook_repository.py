import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook_inbox import WebhookInbox


async def store(
    db: AsyncSession,
    *,
    provider: str,
    event_type: Optional[str],
    signature: Optional[str],
    headers_json: dict,
    payload_json: dict,
    dedupe_key: Optional[str],
    verification_status: str = "pending",
) -> Optional[uuid.UUID]:
    """Insert a raw webhook. Returns the inbox id, or None when the
    (provider, dedupe_key) pair was already seen (provider re-delivery)."""
    stmt = (
        insert(WebhookInbox)
        .values(
            provider=provider,
            event_type=event_type,
            signature=signature,
            headers_json=headers_json,
            payload_json=payload_json,
            dedupe_key=dedupe_key,
            verification_status=verification_status,
        )
        .on_conflict_do_nothing(
            index_elements=["provider", "dedupe_key"],
            index_where=sa_text("dedupe_key IS NOT NULL"),
        )
        .returning(WebhookInbox.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, inbox_id: uuid.UUID) -> Optional[WebhookInbox]:
    result = await db.execute(
        select(WebhookInbox).where(WebhookInbox.id == inbox_id)
    )
    return result.scalar_one_or_none()


async def set_verification(
    db: AsyncSession, inbox_id: uuid.UUID, verification_status: str
) -> None:
    row = await get_by_id(db, inbox_id)
    if row is not None:
        row.verification_status = verification_status


async def mark_processed(
    db: AsyncSession, inbox_id: uuid.UUID, *, error_message: Optional[str] = None
) -> None:
    row = await get_by_id(db, inbox_id)
    if row is not None:
        row.processing_status = "processed"
        row.processed_at = datetime.now(timezone.utc)
        row.error_message = error_message


async def mark_failed(
    db: AsyncSession, inbox_id: uuid.UUID, *, error_message: str
) -> None:
    row = await get_by_id(db, inbox_id)
    if row is not None:
        row.processing_status = "failed"
        row.processed_at = datetime.now(timezone.utc)
        row.error_message = error_message[:2000]
