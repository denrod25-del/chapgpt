"""Block startup until Postgres is reachable. Exits non-zero if it never comes up.

Run before `alembic upgrade head` in the container entrypoint.
"""
import asyncio
import sys

from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine

MAX_ATTEMPTS = 30
DELAY_SECONDS = 2.0


async def _check() -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def main() -> int:
    # Dispose the engine inside this same event loop (a second asyncio.run would
    # dispose it on a different loop → noisy "event loop is closed" errors).
    try:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                await _check()
                print(f"[prestart] database reachable ({settings.APP_NAME}) — ready.")
                return 0
            except Exception as exc:  # noqa: BLE001 — boundary: any error means "not ready"
                print(f"[prestart] attempt {attempt}/{MAX_ATTEMPTS}: DB not ready ({exc})")
                if attempt < MAX_ATTEMPTS:
                    await asyncio.sleep(DELAY_SECONDS)
        print("[prestart] database unreachable after retries — giving up.", file=sys.stderr)
        return 1
    finally:
        await engine.dispose()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
