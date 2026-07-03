"""Async Postgres pool (asyncpg). Single source of truth for connections."""
import asyncpg
from ..config import config

_pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    """Create the connection pool once at startup. Bounded size."""
    global _pool
    assert config.DATABASE_URL, "DATABASE_URL required to init pool"
    if _pool is None:
        _pool = await asyncpg.create_pool(config.DATABASE_URL, min_size=2, max_size=10)


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    assert _pool is not None, "pool not initialized; call init_pool() at startup"
    return _pool
