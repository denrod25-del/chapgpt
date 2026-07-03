"""Lead intake (Automation #1 + #8 trigger). Thin handler: persist in a txn,
comms run as a BackgroundTask, response waits only on Postgres."""
from fastapi import APIRouter, BackgroundTasks, Depends

from ...core.idempotency import IdemGuard, idem_guard
from ...db.session import get_pool
from ...models import repo
from ...schemas.leads import LeadIn, LeadOut
from ...services import lead_flow

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadOut, status_code=201)
async def create_lead(lead: LeadIn, background: BackgroundTasks,
                      idem: IdemGuard = Depends(idem_guard)) -> LeadOut:
    """Intake a website lead: persist, tag, emit events; confirm + alert async."""
    if idem.replay is not None:
        return LeadOut(**idem.replay)

    pool = get_pool()
    is_emergency = (lead.urgency.value == "emergency"
                    or lead.service_type.value == "emergency")

    async with pool.acquire() as conn:
        async with conn.transaction():
            lead_id = await repo.upsert_lead(conn, lead)
            await repo.emit_event(conn, "form_submitted", lead_id=lead_id,
                                  payload=lead.model_dump())
            await repo.emit_event(conn, "lead_created", lead_id=lead_id,
                                  payload={"service_type": lead.service_type.value,
                                           "urgency": lead.urgency.value,
                                           "source": lead.source})
            await repo.add_tag(conn, "lead-new", lead_id=lead_id)
            if is_emergency:
                await repo.add_tag(conn, "emergency", lead_id=lead_id)
            if lead.water_source.value == "well":
                await repo.add_tag(conn, "well-water", lead_id=lead_id)
            elif lead.water_source.value == "city":
                await repo.add_tag(conn, "city-water", lead_id=lead_id)

    # External I/O off the request path — never inside the txn, never blocking the 201.
    background.add_task(lead_flow.run_new_lead_comms, lead, lead_id, is_emergency)

    out = LeadOut(id=lead_id, status="new")
    await idem.store(201, out.model_dump())
    return out
