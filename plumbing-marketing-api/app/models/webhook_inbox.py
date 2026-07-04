from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base, CreatedAtMixin, UUIDPKMixin


class WebhookInbox(UUIDPKMixin, CreatedAtMixin, Base):
    """Raw inbound webhook store: insert first, ack fast, process async."""

    __tablename__ = "webhook_inbox"
    __table_args__ = (
        Index(
            "ix_webhook_inbox_provider_dedupe", "provider", "dedupe_key",
            unique=True, postgresql_where=text("dedupe_key IS NOT NULL"),
        ),
        Index(
            "ix_webhook_inbox_pending", "processing_status", "received_at",
            postgresql_where=text("processing_status IN ('received','failed')"),
        ),
    )

    provider: Mapped[str] = mapped_column(Text, nullable=False)
    event_type: Mapped[str | None] = mapped_column(Text)
    signature: Mapped[str | None] = mapped_column(Text)
    headers_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    payload_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    processing_status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'received'")
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    dedupe_key: Mapped[str | None] = mapped_column(Text)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
