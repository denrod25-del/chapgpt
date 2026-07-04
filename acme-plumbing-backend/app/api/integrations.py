"""Internal integration routes (called by n8n). Bearer-auth protected.

No /integrations/mailgun/send-email: transactional email goes through Resend;
Mailgun stays webhook-inbound only."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_internal
from app.deps import get_db
from app.schemas.integration import (
    BrevoContactSync,
    BrevoContactSyncOut,
    EmailSend,
    EmailSendOut,
    SmsSend,
    SmsSendOut,
)
from app.services import integration_service

router = APIRouter(prefix="/integrations", tags=["integrations"],
                   dependencies=[Depends(require_internal)])


@router.post("/gatewayapi/send-sms", response_model=SmsSendOut)
async def send_sms(payload: SmsSend, db: AsyncSession = Depends(get_db)) -> SmsSendOut:
    return await integration_service.send_sms(db, payload)


@router.post("/resend/send-email", response_model=EmailSendOut)
async def send_email(payload: EmailSend, db: AsyncSession = Depends(get_db)) -> EmailSendOut:
    return await integration_service.send_email(db, payload)


@router.post("/brevo/sync-contact", response_model=BrevoContactSyncOut)
async def sync_contact(
    payload: BrevoContactSync, db: AsyncSession = Depends(get_db)
) -> BrevoContactSyncOut:
    return await integration_service.sync_brevo_contact(db, payload)
