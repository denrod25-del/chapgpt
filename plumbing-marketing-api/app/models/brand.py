from sqlalchemy import Boolean, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class Brand(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "brands"

    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    website_domain: Mapped[str | None] = mapped_column(Text)
    primary_city: Mapped[str | None] = mapped_column(Text)
    primary_state: Mapped[str | None] = mapped_column(String(2))
    phone: Mapped[str | None] = mapped_column(Text)
    default_from_email: Mapped[str | None] = mapped_column(Text)
    default_from_name: Mapped[str | None] = mapped_column(Text)
    timezone: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'America/New_York'")
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )

    contacts: Mapped[list["Contact"]] = relationship(  # noqa: F821
        back_populates="brand", cascade="all, delete-orphan"
    )
