import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, uuid_pk


class ReviewRequest(Base, TimestampMixin):
    """A scheduled review ask. Created on job/booking completion, dispatched by
    n8n once `scheduled_for` passes. status flows:
    pending → due → sent → delivered → clicked → completed (or failed/canceled)."""

    __tablename__ = "review_requests"
    __table_args__ = (
        # Fast "what's due now" scan for the n8n poller.
        Index(
            "idx_review_requests_due", "status", "scheduled_for",
            postgresql_where=text("status IN ('pending','due')"),
        ),
        Index("idx_review_requests_brand", "brand_id", "created_at"),
        Index("idx_review_requests_contact", "contact_id"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL")
    )
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="SET NULL")
    )
    communication_log_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("communication_logs.id", ondelete="SET NULL")
    )
    channel: Mapped[str] = mapped_column(Text, nullable=False)          # email | sms
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'pending'")
    )
    review_url: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failure_reason: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
