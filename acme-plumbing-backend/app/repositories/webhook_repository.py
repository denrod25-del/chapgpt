import uuid
from typing import Optional

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
        )
        .on_conflict_do_nothing(
            index_elements=["provider", "dedupe_key"],
            index_where=sa_text("dedupe_key IS NOT NULL"),
        )
        .returning(WebhookInbox.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
