"""webhooks_inbox data access (migration 005). SQL only — processing lives in app/webhooks."""
import json
from typing import Optional

import asyncpg


async def store_inbox(conn: asyncpg.Connection, *, provider: str, event_type: str,
                      dedupe_key: Optional[str], signature_valid: Optional[bool],
                      headers: dict, payload: dict, raw_body: str) -> Optional[str]:
    """Insert the raw webhook. Returns inbox id, or None when it's a duplicate
    (unique index on (provider, dedupe_key) absorbs provider re-deliveries)."""
    row = await conn.fetchrow(
        """INSERT INTO webhooks_inbox
             (provider, event_type, dedupe_key, signature_valid, headers, payload, raw_body)
           VALUES ($1,$2,$3,$4,$5::jsonb,$6::jsonb,$7)
           ON CONFLICT (provider, dedupe_key) WHERE dedupe_key IS NOT NULL DO NOTHING
           RETURNING id""",
        provider, event_type, dedupe_key, signature_valid,
        json.dumps(headers), json.dumps(payload, default=str), raw_body)
    return str(row["id"]) if row else None


async def claim_for_processing(conn: asyncpg.Connection,
                               inbox_id: str) -> Optional[asyncpg.Record]:
    """Claim a row via status flip so an inline task and a drainer worker never
    double-process. Bounded attempts."""
    return await conn.fetchrow(
        """UPDATE webhooks_inbox SET status='processing', attempts=attempts+1
           WHERE id=$1 AND status IN ('received','failed') AND attempts < 5
           RETURNING provider, event_type, payload""",
        inbox_id)


async def mark_processed(conn: asyncpg.Connection, inbox_id: str) -> None:
    await conn.execute(
        "UPDATE webhooks_inbox SET status='processed', processed_at=now() WHERE id=$1",
        inbox_id)


async def mark_failed(conn: asyncpg.Connection, inbox_id: str, error: str) -> None:
    await conn.execute(
        "UPDATE webhooks_inbox SET status='failed', error=$2 WHERE id=$1",
        inbox_id, error[:500])
