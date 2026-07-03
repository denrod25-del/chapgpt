"""Generic event ingestion — call_clicked, page views, etc. from the frontend.
Event names are validated by the taxonomy CHECK constraint (migration 005)."""
from fastapi import APIRouter, HTTPException

import asyncpg

from ...db.session import get_pool
from ...models import repo
from ...schemas.leads import EventIn

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", status_code=201)
async def ingest_event(evt: EventIn) -> dict:
    """Append a client-emitted event to the canonical log."""
    pool = get_pool()
    async with pool.acquire() as conn:
        try:
            await repo.emit_event(conn, evt.event_name, lead_id=evt.lead_id,
                                  customer_id=evt.customer_id, payload=evt.payload,
                                  source_system=evt.source_system or "frontend")
        except asyncpg.CheckViolationError:
            raise HTTPException(422, f"unknown event_name '{evt.event_name}' (see taxonomy)")
    return {"ok": True}
