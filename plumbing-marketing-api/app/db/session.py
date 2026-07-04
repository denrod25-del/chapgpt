"""Async engine + session factory + FastAPI dependency."""
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.core.config import settings

engine = create_async_engine(
    settings.async_database_url,
    echo=settings.APP_DEBUG,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
)

SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """One AsyncSession per request. Services own commit/rollback."""
    async with SessionLocal() as session:
        yield session
