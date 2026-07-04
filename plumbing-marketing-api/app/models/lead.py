import uuid
from typing import Any

from sqlalchemy import ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class Lead(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "leads"
    __table_args__ = (
        Index("ix_leads_brand_status_created", "brand_id", "status", "created_at"),
        Index("ix_leads_contact_id", "contact_id"),
        Index(
            "ix_leads_idempotency_key", "idempotency_key",
            unique=True, postgresql_where=text("idempotency_key IS NOT NULL"),
        ),
    )

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contacts.id", ondelete="SET NULL")
    )
    lead_type: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'website_form'")
    )
    source: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'website'")
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'new'")
    )
    service_type: Mapped[str | None] = mapped_column(Text)
    urgency: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'standard'")
    )
    message: Mapped[str | None] = mapped_column(Text)
    page_url: Mapped[str | None] = mapped_column(Text)
    utm_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    meta_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    idempotency_key: Mapped[str | None] = mapped_column(Text)
