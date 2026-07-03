"""Inbound webhook endpoints — one per provider. Thin: verify + store + ack;
all processing lives in inbox.py handlers. Paths kept stable with the pre-v1 backend."""
import base64
import hashlib
import hmac
import logging
import time
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Request

from ..core.config import config
from ..db.session import get_pool
from ..models import repo
from ..schemas.leads import LeadIn
from ..services import lead_flow
from .inbox import parse_body, receive_webhook

log = logging.getLogger("wiyw.webhooks")
router = APIRouter(prefix="/webhooks", tags=["webhooks"])

_MAX_SIG_AGE_S = 300    # replay window for timestamped signatures


# ── verifiers ────────────────────────────────────────────────────────

async def _verify_brevo(req: Request, raw: bytes) -> Optional[bool]:
    """Brevo sends no HMAC; require the shared token set in the webhook URL (?token=)."""
    if not config.BREVO_WEBHOOK_TOKEN:
        return None
    return hmac.compare_digest(req.query_params.get("token", ""),
                               config.BREVO_WEBHOOK_TOKEN)


async def _verify_gatewayapi(req: Request, raw: bytes) -> Optional[bool]:
    """GatewayAPI sends no HMAC; require the shared secret set in the webhook URL."""
    if not config.GATEWAYAPI_WEBHOOK_SECRET:
        return None
    return hmac.compare_digest(req.query_params.get("token", ""),
                               config.GATEWAYAPI_WEBHOOK_SECRET)


async def _verify_mailgun(req: Request, raw: bytes) -> Optional[bool]:
    """HMAC-SHA256 of timestamp+token with the API key; 5-min replay window."""
    if not config.MAILGUN_API_KEY:
        return None
    payload = parse_body(raw, req.headers.get("content-type", ""))
    sig = payload.get("signature", {})
    if not isinstance(sig, dict):       # legacy form posts: flat fields
        sig = payload
    timestamp = str(sig.get("timestamp", ""))
    token = str(sig.get("token", ""))
    signature = str(sig.get("signature", ""))
    if not (timestamp and token and signature):
        return False
    if abs(time.time() - float(timestamp)) > _MAX_SIG_AGE_S:
        return False
    expected = hmac.new(config.MAILGUN_API_KEY.encode(),
                        f"{timestamp}{token}".encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)


async def _verify_resend(req: Request, raw: bytes) -> Optional[bool]:
    """Svix signature: HMAC-SHA256 of '{id}.{timestamp}.{body}' with the whsec_ key."""
    if not config.RESEND_WEBHOOK_SECRET:
        return None
    svix_id = req.headers.get("svix-id", "")
    svix_ts = req.headers.get("svix-timestamp", "")
    svix_sig = req.headers.get("svix-signature", "")
    if not (svix_id and svix_ts and svix_sig):
        return False
    if abs(time.time() - float(svix_ts)) > _MAX_SIG_AGE_S:
        return False
    secret = config.RESEND_WEBHOOK_SECRET.removeprefix("whsec_")
    signed = f"{svix_id}.{svix_ts}.".encode() + raw
    expected = base64.b64encode(
        hmac.new(base64.b64decode(secret), signed, hashlib.sha256).digest()).decode()
    # Header may hold several space-separated 'v1,<sig>' entries (key rotation).
    return any(hmac.compare_digest(part.split(",", 1)[-1], expected)
               for part in svix_sig.split(" ") if part)


async def _verify_storyblok(req: Request, raw: bytes) -> Optional[bool]:
    """HMAC-SHA1 of the raw body with the webhook secret."""
    if not config.STORYBLOK_WEBHOOK_SECRET:
        return None
    expected = hmac.new(config.STORYBLOK_WEBHOOK_SECRET.encode(), raw, hashlib.sha1).hexdigest()
    return hmac.compare_digest(req.headers.get("webhook-signature", ""), expected)


async def _verify_forms(req: Request, raw: bytes) -> Optional[bool]:
    """Third-party form vendors: shared token in the URL."""
    if not config.FORMS_WEBHOOK_TOKEN:
        return None
    return hmac.compare_digest(req.query_params.get("token", ""),
                               config.FORMS_WEBHOOK_TOKEN)


# ── endpoints ────────────────────────────────────────────────────────

@router.post("/brevo")
async def brevo_webhook(req: Request, background: BackgroundTasks) -> dict:
    return await receive_webhook(
        req, background, provider="brevo", verifier=_verify_brevo,
        dedupe_from=lambda p, raw: str(p.get("id") or hashlib.md5(raw).hexdigest()),
        event_type_from=lambda p: str(p.get("event", "unknown")))


@router.post("/gatewayapi")
async def gatewayapi_webhook(req: Request, background: BackgroundTasks) -> dict:
    return await receive_webhook(
        req, background, provider="gatewayapi", verifier=_verify_gatewayapi,
        # One DLR per (message, state); inbound MO messages dedupe on body hash.
        dedupe_from=lambda p, raw: (f"{p['id']}:{p.get('status','')}" if p.get("id")
                                    else hashlib.md5(raw).hexdigest()),
        event_type_from=lambda p: str(p.get("status") or ("inbound" if p.get("message") else "unknown")).lower())


@router.post("/resend")
async def resend_webhook(req: Request, background: BackgroundTasks) -> dict:
    return await receive_webhook(
        req, background, provider="resend", verifier=_verify_resend,
        dedupe_from=lambda p, raw: req.headers.get("svix-id") or hashlib.md5(raw).hexdigest(),
        event_type_from=lambda p: str(p.get("type", "unknown")))


@router.post("/mailgun")
async def mailgun_webhook(req: Request, background: BackgroundTasks) -> dict:
    def _dedupe(p: dict, raw: bytes) -> str:
        sig = p.get("signature", {})
        token = sig.get("token") if isinstance(sig, dict) else p.get("token")
        return str(token) if token else hashlib.md5(raw).hexdigest()

    def _etype(p: dict) -> str:
        ed = p.get("event-data", {})
        return str(ed.get("event") or ("inbound" if p.get("body-plain") else "unknown")).lower()

    return await receive_webhook(req, background, provider="mailgun",
                                 verifier=_verify_mailgun,
                                 dedupe_from=_dedupe, event_type_from=_etype)


@router.post("/storyblok")
async def storyblok_webhook(req: Request, background: BackgroundTasks) -> dict:
    return await receive_webhook(
        req, background, provider="storyblok", verifier=_verify_storyblok,
        dedupe_from=lambda p, raw: (f"{p['story_id']}:{p.get('action','')}:{p.get('published_at','')}"
                                    if p.get("story_id") else hashlib.md5(raw).hexdigest()),
        event_type_from=lambda p: str(p.get("action", "unknown")))


@router.post("/forms", status_code=201)
async def forms_webhook(req: Request, background: BackgroundTasks) -> dict:
    """External form vendors → normalized lead. Stores raw first (audit), then runs
    the standard lead flow — same validation and comms as POST /leads."""
    receipt = await receive_webhook(
        req, background, provider="forms", verifier=_verify_forms,
        dedupe_from=lambda p, raw: str(p.get("submission_id") or hashlib.md5(raw).hexdigest()),
        event_type_from=lambda p: "form_submission")
    if receipt.get("duplicate") or not receipt.get("inbox_id"):
        return receipt

    payload = parse_body(await req.body(), req.headers.get("content-type", ""))
    try:
        lead = LeadIn(**{k: payload[k] for k in LeadIn.model_fields if k in payload})
    except Exception as e:              # noqa: BLE001 — vendor payloads vary; keep raw row
        log.error("forms webhook payload not lead-shaped: %s", e)
        return {**receipt, "lead_created": False}

    is_emergency = (lead.urgency.value == "emergency"
                    or lead.service_type.value == "emergency")
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            lead_id = await repo.upsert_lead(conn, lead)
            await repo.emit_event(conn, "form_submitted", lead_id=lead_id,
                                  payload=lead.model_dump(), source_system="forms")
            await repo.add_tag(conn, "lead-new", lead_id=lead_id)
            if is_emergency:
                await repo.add_tag(conn, "emergency", lead_id=lead_id)
    background.add_task(lead_flow.run_new_lead_comms, lead, lead_id, is_emergency)
    return {**receipt, "lead_created": True, "lead_id": lead_id}
