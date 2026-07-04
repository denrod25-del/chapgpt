import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin, UUIDPKMixin


class CommunicationLog(UUIDPKMixin, CreatedAtMixin, Base):
    """One row per message in/out. Append-mostly (no updated_at)."""

    __tablename__ = "communication_logs"
    __table_args__ = (
        Index("ix_communication_logs_external_message_id", "external_message_id"),
        Index("ix_communication_logs_brand_created", "brand_id", "created_at"),
        Index("ix_communication_logs_contact_id", "contact_id"),
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
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    direction: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'outbound'")
    )
    template_key: Mapped[str | None] = mapped_column(Text)
    external_message_id: Mapped[str | None] = mapped_column(Text)
    delivery_status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'queued'")
    )
    subject: Mapped[str | None] = mapped_column(Text)
    body_preview: Mapped[str | None] = mapped_column(String(500))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
