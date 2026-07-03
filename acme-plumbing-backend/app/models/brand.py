import uuid

from sqlalchemy import Boolean, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, uuid_pk


class Brand(Base, TimestampMixin):
    __tablename__ = "brands"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    website_domain: Mapped[str | None] = mapped_column(Text)
    primary_city: Mapped[str | None] = mapped_column(Text)
    primary_state: Mapped[str | None] = mapped_column(String(2))
    phone: Mapped[str | None] = mapped_column(Text)               # E.164
    default_from_email: Mapped[str | None] = mapped_column(Text)
    default_from_name: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
