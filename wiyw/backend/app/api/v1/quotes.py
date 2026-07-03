"""Quote requests (Automation #2 trigger) — high-intent lead + follow-up entry."""
from fastapi import APIRouter, BackgroundTasks, Depends

from ...core.idempotency import IdemGuard, idem_guard
from ...db.session import get_pool
from ...models import repo
from ...schemas.leads import QuoteIn
from ...services import lead_flow

router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.post("", status_code=201)
async def request_quote(q: QuoteIn, background: BackgroundTasks,
                        idem: IdemGuard = Depends(idem_guard)) -> dict:
    """Quote request → lead(status=quoted) + quote-pending tag + async ack/alert/Brevo."""
    if idem.replay is not None:
        return idem.replay

    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """INSERT INTO leads (full_name, phone, email, service_type, message,
                                      source, status)
                   VALUES ($1,$2,$3,$4,$5,$6,'quoted') RETURNING id""",
                q.full_name, q.phone, q.email, q.service_type, q.details, q.source)
            assert row is not None, "quote lead insert returned no row"
            lead_id = str(row["id"])
            await repo.emit_event(conn, "quote_requested", lead_id=lead_id,
                                  payload={"service_type": q.service_type})
            await repo.add_tag(conn, "quote-pending", lead_id=lead_id)

    background.add_task(lead_flow.run_quote_comms, q, lead_id)

    out = {"id": lead_id, "status": "quoted"}
    await idem.store(201, out)
    return out
