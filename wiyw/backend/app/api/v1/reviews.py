"""Review capture + manual review-request trigger (split-leg flow, docs/OWNERSHIP.md)."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from ...core.auth import require_internal
from ...core.config import config
from ...db.session import get_pool
from ...models import repo
from ...schemas.reviews import ReviewIn, ReviewRequestOut, ReviewRequestPayload
from ...schemas.webhooks import CommChannel
from ...services import email, sms

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", status_code=201)
async def capture_review(r: ReviewIn) -> dict:
    """Internal review capture (review-gate page or manual entry)."""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO reviews (customer_id, job_id, rating, platform, content, received_at)
               VALUES ($1,$2,$3,$4,$5, now()) RETURNING id""",
            r.customer_id, r.job_id, r.rating, r.platform, r.content)
        assert row is not None, "review insert returned no row"
        await repo.emit_event(conn, "review_received", customer_id=r.customer_id,
                              payload={"rating": r.rating, "platform": r.platform})
    return {"id": str(row["id"])}


@router.post("/request", response_model=ReviewRequestOut,
             dependencies=[Depends(require_internal)])
async def request_review(body: ReviewRequestPayload,
                         background: BackgroundTasks) -> ReviewRequestOut:
    """Manual/immediate review-request trigger. Shares the jobs.review_requested flag
    with n8n WF-2 so the two paths can never double-send. SMS leg when consented
    (GatewayAPI); email leg otherwise (Resend). The delayed nurture leg stays in Brevo."""
    pool = get_pool()
    async with pool.acquire() as conn:
        claim = await repo.claim_review_request(conn, body.job_id)
        if claim is None:
            exists = await conn.fetchval("SELECT 1 FROM jobs WHERE id=$1", body.job_id)
            if not exists:
                raise HTTPException(404, "job not found")
            raise HTTPException(409, "review already requested for this job")

    review_link = f"{config.REVIEW_SHORTLINK_BASE}/{body.job_id}"
    use_sms = (claim["consent_sms"] and claim["phone"]
               and body.channel_override != CommChannel.email)
    channel = CommChannel.sms if use_sms else CommChannel.email

    async def _send() -> None:
        if channel == CommChannel.sms:
            ok, msg_id = await sms.send_sms(
                claim["phone"], sms.review_request_text(claim["full_name"], review_link))
            provider, template, to_addr = "gatewayapi", "sms_review", claim["phone"]
        else:
            ok, _prov = await email.send(
                claim["email"] or "", "How did we do?",
                email.review_request_html(claim["full_name"], review_link))
            msg_id, provider, template, to_addr = None, "resend", "txn_review_request", claim["email"] or ""
        async with pool.acquire() as conn:
            await repo.log_comm(conn, channel=channel.value, direction="outbound",
                                to_addr=to_addr, provider=provider, template=template,
                                status="sent" if ok else "failed", provider_msg_id=msg_id,
                                customer_id=str(claim["customer_id"]))
            await repo.add_tag(conn, "review-requested",
                               customer_id=str(claim["customer_id"]))
            await repo.emit_event(conn, "review_request_sent",
                                  customer_id=str(claim["customer_id"]),
                                  payload={"job_id": body.job_id, "channel": channel.value})

    background.add_task(_send)
    return ReviewRequestOut(job_id=body.job_id, scheduled=True,
                            channel=channel, review_link=review_link)
