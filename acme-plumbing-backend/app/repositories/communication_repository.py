"""communication_logs access for delivery reconciliation.

`create()` is re-exported from comm_repository so callers have one import surface;
the reconciliation-specific reads/updates live here.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication_log import CommunicationLog
from app.repositories.comm_repository import create  # noqa: F401 (re-export)
from app.schemas.provider_events import should_apply_status

__all__ = ["create", "get_by_external_id", "get_by_id", "apply_delivery_update"]


async def get_by_external_id(
    db: AsyncSession, provider: str, external_message_id: str
) -> Optional[CommunicationLog]:
    """Newest row for a provider message id. Provider ids are effectively unique,
    but we order by created_at desc defensively in case of re-sends."""
    result = await db.execute(
        select(CommunicationLog)
        .where(
            CommunicationLog.provider == provider,
            CommunicationLog.external_message_id == external_message_id,
        )
        .order_by(CommunicationLog.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_by_id(
    db: AsyncSession, comm_id: uuid.UUID
) -> Optional[CommunicationLog]:
    result = await db.execute(
        select(CommunicationLog).where(CommunicationLog.id == comm_id)
    )
    return result.scalar_one_or_none()


async def apply_delivery_update(
    row: CommunicationLog,
    *,
    new_status: Optional[str],
    occurred_at: Optional[datetime] = None,
) -> bool:
    """Advance a row's delivery_status if the incoming status is forward-progress
    or a terminal-negative signal. Sets delivered_at on first 'delivered'.
    Returns True if the row was changed. Caller owns commit."""
    if not new_status:
        return False
    if not should_apply_status(row.delivery_status, new_status):
        return False

    row.delivery_status = new_status
    when = occurred_at or datetime.now(timezone.utc)
    if new_status == "delivered" and row.delivered_at is None:
        row.delivered_at = when
    if new_status == "sent" and row.sent_at is None:
        row.sent_at = when
    return True
