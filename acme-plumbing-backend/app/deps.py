"""FastAPI dependencies."""
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal


async def get_db() -> AsyncIterator[AsyncSession]:
    """One AsyncSession per request. Services own commit/rollback; the session
    is rolled back automatically here if a handler raises before committing."""
    async with SessionLocal() as session:
        yield session
