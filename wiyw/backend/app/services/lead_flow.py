"""New-lead / quote business flows (Automations #1, #2, #8 — synchronous tier).
Runs as a BackgroundTask after the DB transaction commits: the 201 response only
waits on Postgres; provider I/O happens here. Do NOT duplicate these sends in n8n."""
import logging

from ..core.config import config
from ..db.session import get_pool
from ..integrations import brevo
from ..models import repo
from ..schemas.leads import LeadIn, QuoteIn
from . import email, sms

log = logging.getLogger("wiyw.lead_flow")


async def run_new_lead_comms(lead: LeadIn, lead_id: str, is_emergency: bool) -> None:
    """Confirmation email+SMS, owner alert, emergency ack, Brevo mirror, comm logs."""
    pool = get_pool()

    ok_email = await email.send_confirmation(
        lead.email or "", lead.full_name, lead.service_type.value)
    ok_sms, msg_id = await sms.send_sms(lead.phone, sms.lead_confirm_text(lead.full_name))

    # Owner alert — always, escalated copy on emergency.
    if config.OWNER_ALERT_PHONE:
        await sms.send_sms(config.OWNER_ALERT_PHONE,
                           sms.owner_alert_text(lead.full_name, lead.service_type.value,
                                                lead.phone, is_emergency))

    # Emergency fast-response promise (Automation #8, synchronous leg).
    if is_emergency:
        await sms.send_sms(lead.phone, sms.emergency_ack_text())

    async with pool.acquire() as conn:
        if ok_sms:
            await repo.log_comm(conn, channel="sms", direction="outbound",
                                to_addr=lead.phone, provider="gatewayapi",
                                template="sms_lead_confirm", status="sent",
                                provider_msg_id=msg_id, lead_id=lead_id)
        if lead.email:
            await repo.log_comm(conn, channel="email", direction="outbound",
                                to_addr=lead.email, provider="resend",
                                template="txn_lead_confirmation",
                                status="sent" if ok_email else "failed",
                                lead_id=lead_id)
        if not (ok_email or ok_sms):
            log.error("ALL comms failed for lead %s", lead_id)

    contact_id = await brevo.upsert_contact(
        lead.email, lead.phone,
        {"SERVICE_TYPE": lead.service_type.value, "URGENCY": lead.urgency.value,
         "SOURCE": lead.source, "CITY": lead.city,
         "WATER_SOURCE": lead.water_source.value, "STATUS": "new"})
    if contact_id:
        async with pool.acquire() as conn:
            await conn.execute("UPDATE leads SET brevo_contact_id=$1 WHERE id=$2",
                               contact_id, lead_id)


async def run_quote_comms(quote: QuoteIn, lead_id: str) -> None:
    """Quote ack SMS, owner alert, Brevo mirror (STATUS=quoted enters wf_quote_followup)."""
    pool = get_pool()

    ok_sms, msg_id = await sms.send_sms(
        quote.phone, sms.quote_ack_text(quote.full_name, quote.service_type))
    if config.OWNER_ALERT_PHONE:
        await sms.send_sms(config.OWNER_ALERT_PHONE,
                           f"Quote request: {quote.full_name} · {quote.service_type} · {quote.phone}")

    async with pool.acquire() as conn:
        if ok_sms:
            await repo.log_comm(conn, channel="sms", direction="outbound",
                                to_addr=quote.phone, provider="gatewayapi",
                                template="sms_quote_ack", status="sent",
                                provider_msg_id=msg_id, lead_id=lead_id)

    contact_id = await brevo.upsert_contact(
        quote.email, quote.phone,
        {"SERVICE_TYPE": quote.service_type, "STATUS": "quoted"})
    if contact_id:
        async with pool.acquire() as conn:
            await conn.execute("UPDATE leads SET brevo_contact_id=$1 WHERE id=$2",
                               contact_id, lead_id)
