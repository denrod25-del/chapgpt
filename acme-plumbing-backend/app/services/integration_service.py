"""Integration send flows: resolve brand → call provider client → log the message.

These are thin provider proxies for n8n. They return 200 even when a provider is
unconfigured (client returns a falsy result) so workflow nodes stay green in dev;
the communication_logs row records whether the send actually succeeded."""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.brevo_client import brevo_client
from app.integrations.gatewayapi_client import gatewayapi_client
from app.integrations.resend_client import resend_client
from app.repositories import comm_repository, get_brand_id_by_slug
from app.schemas.integration import (
    BrevoContactSync,
    BrevoContactSyncOut,
    EmailSend,
    EmailSendOut,
    SmsSend,
    SmsSendOut,
)


async def _brand_id(db: AsyncSession, slug: str):
    brand_id = await get_brand_id_by_slug(db, slug)
    if brand_id is None:
        raise HTTPException(422, f"unknown brand_slug '{slug}'")
    return brand_id


async def send_sms(db: AsyncSession, payload: SmsSend) -> SmsSendOut:
    brand_id = await _brand_id(db, payload.brand_slug)
    ok, msg_id = await gatewayapi_client.send_sms(to=payload.to, message=payload.message)
    await comm_repository.create(
        db, brand_id=brand_id, channel="sms", provider="gatewayapi",
        template_key=payload.template, delivery_status="sent" if ok else "failed",
        to_addr=payload.to, body_preview=payload.message, external_message_id=msg_id,
        metadata_json={"lead_id": payload.lead_id, "customer_id": payload.customer_id},
    )
    await db.commit()
    return SmsSendOut(sent=ok, provider_msg_id=msg_id)


async def send_email(db: AsyncSession, payload: EmailSend) -> EmailSendOut:
    brand_id = await _brand_id(db, payload.brand_slug)
    ok, msg_id = await resend_client.send_email(
        to=payload.to, subject=payload.subject, html=payload.html)
    await comm_repository.create(
        db, brand_id=brand_id, channel="email", provider="resend",
        template_key=payload.template, delivery_status="sent" if ok else "failed",
        to_addr=payload.to, subject=payload.subject, body_preview=payload.html,
        external_message_id=msg_id,
        metadata_json={"lead_id": payload.lead_id, "customer_id": payload.customer_id},
    )
    await db.commit()
    return EmailSendOut(sent=ok, provider="resend", provider_msg_id=msg_id)


async def sync_brevo_contact(db: AsyncSession, payload: BrevoContactSync) -> BrevoContactSyncOut:
    # Validate the brand exists for a consistent error surface, even though the
    # Brevo mirror itself does not write to Postgres.
    await _brand_id(db, payload.brand_slug)
    contact_id = await brevo_client.upsert_contact(
        email=payload.email, phone=payload.phone,
        attributes=payload.attributes, list_ids=payload.list_ids)
    return BrevoContactSyncOut(synced=contact_id is not None, contact_id=contact_id)
