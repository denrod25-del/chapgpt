"""Internal integration routes (n8n → backend). One logging/consent path for all sends.
No /integrations/mailgun/send-email route on purpose: Mailgun is automatic failover
inside the email service (docs/OWNERSHIP.md)."""
from fastapi import APIRouter, Depends

from ...core.auth import require_internal
from ...core.config import config
from ...core.idempotency import IdemGuard, idem_guard
from ...db.session import get_pool
from ...integrations import brevo
from ...models import repo
from ...schemas.integrations import (BrevoContactSync, BrevoContactSyncOut,
                                     EmailSend, EmailSendOut, SmsSend, SmsSendOut)
from ...services import email, sms

router = APIRouter(prefix="/integrations", tags=["integrations"],
                   dependencies=[Depends(require_internal)])


@router.post("/gatewayapi/send-sms", response_model=SmsSendOut)
async def send_sms(body: SmsSend, idem: IdemGuard = Depends(idem_guard)) -> SmsSendOut:
    if idem.replay is not None:
        return SmsSendOut(**idem.replay)
    ok, msg_id = await sms.send_sms(body.to, body.message)
    pool = get_pool()
    async with pool.acquire() as conn:
        await repo.log_comm(conn, channel="sms", direction="outbound", to_addr=body.to,
                            provider="gatewayapi", template=body.template,
                            status="sent" if ok else "failed",
                            provider_msg_id=msg_id, lead_id=body.lead_id,
                            customer_id=body.customer_id)
    out = SmsSendOut(sent=ok, provider_msg_id=msg_id)
    await idem.store(200, out.model_dump())
    return out


@router.post("/resend/send-email", response_model=EmailSendOut)
async def send_email(body: EmailSend, idem: IdemGuard = Depends(idem_guard)) -> EmailSendOut:
    if idem.replay is not None:
        return EmailSendOut(**idem.replay)
    ok, provider = await email.send(body.to, body.subject, body.html)
    pool = get_pool()
    async with pool.acquire() as conn:
        await repo.log_comm(conn, channel="email", direction="outbound", to_addr=body.to,
                            provider=provider or "resend", template=body.template,
                            status="sent" if ok else "failed",
                            lead_id=body.lead_id, customer_id=body.customer_id)
    out = EmailSendOut(sent=ok, provider=provider)
    await idem.store(200, out.model_dump())
    return out


@router.post("/brevo/sync-contact", response_model=BrevoContactSyncOut)
async def sync_contact(body: BrevoContactSync) -> BrevoContactSyncOut:
    """Idempotent by nature (Brevo upsert) — no Idempotency-Key needed."""
    contact_id = await brevo.upsert_contact(
        body.email, body.phone, dict(body.attributes),
        list_ids=body.list_ids or [config.BREVO_LIST_NEW_LEADS])
    if contact_id and body.lead_id:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute("UPDATE leads SET brevo_contact_id=$1 WHERE id=$2",
                               contact_id, body.lead_id)
    return BrevoContactSyncOut(synced=contact_id is not None, contact_id=contact_id)
