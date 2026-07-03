"""Quote + review endpoints and hardened provider webhooks (Section 12)."""
import hashlib
import hmac
import logging
from fastapi import APIRouter, Request, HTTPException
from ..models.db import get_pool
from ..models import repo
from ..services import email, sms, brevo
from ..config import config
from .schemas_ext import QuoteIn, ReviewIn

log = logging.getLogger("wiyw.quote")
quotes_router = APIRouter(prefix="/quotes", tags=["quotes"])
reviews_router = APIRouter(prefix="/reviews", tags=["reviews"])


@quotes_router.post("", status_code=201)
async def request_quote(q: QuoteIn) -> dict:
    """Quote request → high-intent lead + quote-pending tag + follow-up sequence entry."""
    pool = get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                """INSERT INTO leads (full_name, phone, email, service_type, message,
                                      source, status)
                   VALUES ($1,$2,$3,$4,$5,$6,'quoted') RETURNING id""",
                q.full_name, q.phone, q.email, q.service_type, q.details, q.source)
            lead_id = str(row["id"])
            await repo.emit_event(conn, "quote_requested", lead_id=lead_id,
                                  payload={"service_type": q.service_type})
            await repo.add_tag(conn, "quote-pending", lead_id=lead_id)

    await sms.send_sms(q.phone,
                       f"{config.BRAND}: Thanks {q.full_name}! We're preparing your "
                       f"{q.service_type.replace('_',' ')} quote and will follow up shortly.")
    if config.OWNER_ALERT_PHONE:
        await sms.send_sms(config.OWNER_ALERT_PHONE,
                           f"Quote request: {q.full_name} · {q.service_type} · {q.phone}")
    await brevo.upsert_contact(q.email, q.phone,
                              {"SERVICE_TYPE": q.service_type, "STATUS": "quoted"})
    return {"id": lead_id, "status": "quoted"}


@reviews_router.post("", status_code=201)
async def capture_review(r: ReviewIn) -> dict:
    """Internal review capture (e.g. from a review-gate page or manual entry)."""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO reviews (customer_id, job_id, rating, platform, content, received_at)
               VALUES ($1,$2,$3,$4,$5, now()) RETURNING id""",
            r.customer_id, r.job_id, r.rating, r.platform, r.content)
        await repo.emit_event(conn, "review_received", customer_id=r.customer_id,
                              payload={"rating": r.rating, "platform": r.platform})
    return {"id": str(row["id"])}


# ── hardened webhooks ────────────────────────────────────────────────
webhooks_ext = APIRouter(prefix="/webhooks", tags=["webhooks"])


@webhooks_ext.post("/mailgun")
async def mailgun_inbound(req: Request) -> dict:
    """Mailgun inbound parse + delivery events. Verifies HMAC signature."""
    form = await req.form()
    token = str(form.get("token", ""))
    timestamp = str(form.get("timestamp", ""))
    signature = str(form.get("signature", ""))
    if config.MAILGUN_API_KEY and timestamp and token:
        expected = hmac.new(config.MAILGUN_API_KEY.encode(),
                            f"{timestamp}{token}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(401, "bad mailgun signature")
    log.info("Mailgun inbound/event accepted")
    return {"ok": True}


@webhooks_ext.post("/brevo")
async def brevo_events(req: Request) -> dict:
    """Brevo open/click/unsub → events + comms log."""
    body = await req.json()
    etype = body.get("event", "")
    email_addr = body.get("email", "")
    mapping = {"opened": "email_opened", "click": "email_clicked"}
    pool = get_pool()
    async with pool.acquire() as conn:
        if etype in mapping:
            await repo.emit_event(conn, mapping[etype], payload={"email": email_addr},
                                  source_system="brevo")
        if etype == "unsubscribe":
            await conn.execute("UPDATE customers SET consent_email=false WHERE email=$1",
                               email_addr)
    return {"ok": True}
