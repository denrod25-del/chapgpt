"""Lead intake. Runs Automations 1 (new lead) and 8 (emergency fast-response)."""
import logging
from fastapi import APIRouter, HTTPException
from ..models.db import get_pool
from ..models import repo
from ..models.schemas import LeadIn, LeadOut
from ..services import email, sms, brevo
from ..config import config

log = logging.getLogger("wiyw.leads")
router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadOut, status_code=201)
async def create_lead(lead: LeadIn) -> LeadOut:
    """Intake a website lead: persist, confirm to customer, alert owner, sync Brevo."""
    pool = get_pool()
    is_emergency = (lead.urgency.value == "emergency"
                    or lead.service_type.value == "emergency")

    async with pool.acquire() as conn:
        async with conn.transaction():
            lead_id = await repo.upsert_lead(conn, lead)
            await repo.emit_event(conn, "form_submitted", lead_id=lead_id,
                                  payload=lead.model_dump())
            await repo.add_tag(conn, "lead-new", lead_id=lead_id)
            if is_emergency:
                await repo.add_tag(conn, "emergency", lead_id=lead_id)
            if lead.water_source.value == "well":
                await repo.add_tag(conn, "well-water", lead_id=lead_id)
            elif lead.water_source.value == "city":
                await repo.add_tag(conn, "city-water", lead_id=lead_id)

    # Comms happen outside the txn (external I/O must not hold DB locks).
    ok_email = await email.send_confirmation(
        lead.email or "", lead.full_name, lead.service_type.value)
    ok_sms, msg_id = await sms.send_sms(lead.phone, sms.lead_confirm_text(lead.full_name))

    # Owner alert — always, escalate on emergency.
    if config.OWNER_ALERT_PHONE:
        await sms.send_sms(config.OWNER_ALERT_PHONE,
                           sms.owner_alert_text(lead.full_name, lead.service_type.value,
                                                lead.phone, is_emergency))

    # If lead is emergency, send the fast-response promise SMS.
    if is_emergency:
        await sms.send_sms(lead.phone,
                           f"{config.BRAND}: We received your emergency request — "
                           f"we'll call you within 5 minutes. Or call us now: {config.BRAND_PHONE}")

    async with pool.acquire() as conn:
        if ok_sms:
            await repo.log_comm(conn, channel="sms", direction="outbound",
                                to_addr=lead.phone, provider="gatewayapi",
                                template="sms_lead_confirm", status="sent",
                                provider_msg_id=msg_id, lead_id=lead_id)
        if not (ok_email or ok_sms):
            log.error("ALL comms failed for lead %s", lead_id)

    contact_id = await brevo.upsert_contact(
        lead.email, lead.phone,
        {"SERVICE_TYPE": lead.service_type.value, "URGENCY": lead.urgency.value,
         "SOURCE": lead.source, "CITY": lead.city, "WATER_SOURCE": lead.water_source.value})
    if contact_id:
        async with pool.acquire() as conn:
            await conn.execute("UPDATE leads SET brevo_contact_id=$1 WHERE id=$2",
                               contact_id, lead_id)

    return LeadOut(id=lead_id, status="new")
