import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base, CreatedAtMixin, UUIDPKMixin


class EventLog(UUIDPKMixin, CreatedAtMixin, Base):
    """Append-only canonical event log (no updated_at)."""

    __tablename__ = "event_log"
    __table_args__ = (
        Index("ix_event_log_brand_name_time", "brand_id", "event_name", "occurred_at"),
        Index("ix_event_log_lead_id", "lead_id"),
        Index("ix_event_log_payload_gin", "payload_json", postgresql_using="gin"),
    )

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL")
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL")
    )
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="SET NULL")
    )
    event_name: Mapped[str] = mapped_column(Text, nullable=False)
    event_source: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'backend'")
    )
    payload_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
