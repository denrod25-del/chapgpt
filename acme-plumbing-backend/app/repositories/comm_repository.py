import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication_log import CommunicationLog


async def create(
    db: AsyncSession,
    *,
    brand_id: uuid.UUID,
    channel: str,                       # 'email' | 'sms'
    provider: str,                      # 'gatewayapi' | 'resend' | 'brevo' | ...
    template_key: Optional[str],
    delivery_status: str,               # 'sent' | 'failed' | 'queued' | ...
    to_addr: Optional[str] = None,
    subject: Optional[str] = None,
    body_preview: Optional[str] = None,
    external_message_id: Optional[str] = None,
    metadata_json: Optional[dict[str, Any]] = None,
) -> CommunicationLog:
    """Record one outbound message. Caller-supplied lead/customer ids go in
    metadata_json (not the typed FK columns) so a generic send endpoint can't
    trip a foreign-key violation on an id it didn't create."""
    meta = dict(metadata_json or {})
    if to_addr:
        meta.setdefault("to", to_addr)
    row = CommunicationLog(
        brand_id=brand_id,
        channel=channel,
        provider=provider,
        direction="outbound",
        template_key=template_key,
        external_message_id=external_message_id,
        delivery_status=delivery_status,
        subject=subject,
        body_preview=(body_preview or "")[:500] or None,
        metadata_json=meta,
        sent_at=datetime.now(timezone.utc) if delivery_status == "sent" else None,
    )
    db.add(row)
    await db.flush()
    return row
