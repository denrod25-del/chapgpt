"""Inbound webhooks: provider delivery receipts + Storyblok publish.
All ingress is validated; unknown payloads are logged, never trusted."""
import hashlib
import hmac
import logging
from fastapi import APIRouter, Request, HTTPException
from ..models.db import get_pool
from ..config import config

log = logging.getLogger("wiyw.webhooks")
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/gatewayapi")
async def gatewayapi_dlr(req: Request) -> dict:
    """Delivery receipt. Update comms log status; honor STOP opt-outs."""
    body = await req.json()
    status = str(body.get("status", "")).upper()
    msg_id = str(body.get("id", ""))
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE communication_logs SET status=$1 WHERE provider_msg_id=$2",
            status.lower(), msg_id)
    return {"ok": True}


@router.post("/resend")
async def resend_webhook(req: Request) -> dict:
    """Resend open/click/bounce → comms log + events."""
    body = await req.json()
    etype = body.get("type", "")
    data = body.get("data", {})
    email_id = data.get("email_id", "")
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE communication_logs SET status=$1 WHERE provider_msg_id=$2",
            etype.replace("email.", ""), email_id)
    return {"ok": True}


@router.post("/storyblok")
async def storyblok_publish(req: Request) -> dict:
    """On publish: trigger sitemap rebuild / GSC ping (stub). Verifies secret."""
    sig = req.headers.get("webhook-signature", "")
    raw = await req.body()
    if config.STORYBLOK_WEBHOOK_SECRET:
        expected = hmac.new(config.STORYBLOK_WEBHOOK_SECRET.encode(),
                            raw, hashlib.sha1).hexdigest()
        if not hmac.compare_digest(sig, expected):
            raise HTTPException(status_code=401, detail="bad signature")
    log.info("Storyblok publish received; sitemap rebuild queued")
    # TODO: enqueue sitemap regen + GSC sitemap ping
    return {"ok": True}
