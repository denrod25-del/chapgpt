"""Generic event ingestion — call_clicked, page views, etc. from the frontend."""
from fastapi import APIRouter
from ..models.db import get_pool
from ..models import repo
from ..models.schemas import EventIn

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", status_code=201)
async def ingest_event(evt: EventIn) -> dict:
    """Append a client-emitted event to the canonical log."""
    pool = get_pool()
    async with pool.acquire() as conn:
        await repo.emit_event(conn, evt.event_name, lead_id=evt.lead_id,
                              customer_id=evt.customer_id, payload=evt.payload,
                              source_system=evt.source_system or "frontend")
    return {"ok": True}
