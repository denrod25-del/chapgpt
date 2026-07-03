"""Provider webhook receivers. Thin: everything happens in webhook_service."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.schemas.webhook import WebhookReceiptResponse
from app.services import webhook_service

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/brevo", response_model=WebhookReceiptResponse)
async def brevo_webhook(
    request: Request, db: AsyncSession = Depends(get_db)
) -> WebhookReceiptResponse:
    """Brevo events (opened, click, delivered, unsubscribe, hard_bounce)."""
    return await webhook_service.receive_webhook(db, "brevo", request)


@router.post("/mailgun", response_model=WebhookReceiptResponse)
async def mailgun_webhook(
    request: Request, db: AsyncSession = Depends(get_db)
) -> WebhookReceiptResponse:
    """Mailgun delivery events (delivered, failed, complained) + inbound parse."""
    return await webhook_service.receive_webhook(db, "mailgun", request)


@router.post("/gatewayapi", response_model=WebhookReceiptResponse)
async def gatewayapi_webhook(
    request: Request, db: AsyncSession = Depends(get_db)
) -> WebhookReceiptResponse:
    """GatewayAPI SMS delivery reports + inbound MO messages (STOP handling later)."""
    return await webhook_service.receive_webhook(db, "gatewayapi", request)
