import uuid
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class Contact(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "contacts"
    __table_args__ = (
        CheckConstraint(
            "email IS NOT NULL OR phone IS NOT NULL", name="email_or_phone"
        ),
        Index(
            "ix_contacts_brand_email", "brand_id", "email",
            unique=True, postgresql_where=text("email IS NOT NULL"),
        ),
        Index(
            "ix_contacts_brand_phone", "brand_id", "phone",
            unique=True, postgresql_where=text("phone IS NOT NULL"),
        ),
    )

    brand_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    first_name: Mapped[str] = mapped_column(Text, nullable=False)
    last_name: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'website'")
    )
    tags_json: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    external_refs_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )

    brand: Mapped["Brand"] = relationship(back_populates="contacts")  # noqa: F821
