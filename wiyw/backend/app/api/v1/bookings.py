"""Bookings + jobs (Automation #3 trigger; job completion feeds the review flow)."""
import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ...core.config import config
from ...db.session import get_pool
from ...models import repo
from ...schemas.bookings import (BookingIn, BookingOut, BookingStatusUpdate,
                                 JobComplete, JobIn)
from ...services import email, sms

log = logging.getLogger("wiyw.bookings")
bookings_router = APIRouter(prefix="/bookings", tags=["bookings"])
jobs_router = APIRouter(prefix="/jobs", tags=["jobs"])


async def _send_booking_comms(phone: str, email_addr: str | None, name: str,
                              service: str, when: str, booking_id: str,
                              customer_id: str) -> None:
    ok_sms, msg_id = await sms.send_sms(phone, sms.booking_confirm_text(service, when))
    if email_addr:
        await email.send_confirmation(email_addr, name, service)
    pool = get_pool()
    async with pool.acquire() as conn:
        if ok_sms:
            await repo.log_comm(conn, channel="sms", direction="outbound",
                                to_addr=phone, provider="gatewayapi",
                                template="sms_booking_confirm", status="sent",
                                provider_msg_id=msg_id, customer_id=customer_id)


@bookings_router.post("", status_code=201)
async def create_booking(b: BookingIn, background: BackgroundTasks) -> dict:
    """Create booking → Automation #3: confirmation email + SMS (async)."""
    pool = get_pool()
    async with pool.acquire() as conn:
        cust = await conn.fetchrow(
            "SELECT full_name, phone, email FROM customers WHERE id=$1", b.customer_id)
        if not cust:
            raise HTTPException(404, "customer not found")
        row = await conn.fetchrow(
            """INSERT INTO bookings (customer_id, lead_id, scheduled_for, service_type)
               VALUES ($1,$2,$3,$4) RETURNING id""",
            b.customer_id, b.lead_id, b.scheduled_for, b.service_type)
        assert row is not None, "booking insert returned no row"
        booking_id = str(row["id"])
        await repo.emit_event(conn, "appointment_booked", customer_id=b.customer_id,
                              payload={"booking_id": booking_id,
                                       "scheduled_for": b.scheduled_for.isoformat()})
        await repo.add_tag(conn, "booked", customer_id=b.customer_id)

    when = b.scheduled_for.strftime("%b %d at %I:%M %p")
    background.add_task(_send_booking_comms, cust["phone"], cust["email"],
                        cust["full_name"], b.service_type, when, booking_id,
                        b.customer_id)
    return {"id": booking_id, "status": "scheduled"}


@bookings_router.get("/{booking_id}", response_model=BookingOut)
async def get_booking(booking_id: str) -> BookingOut:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await repo.fetch_booking(conn, booking_id)
    if not row:
        raise HTTPException(404, "booking not found")
    return BookingOut(**{**dict(row), "id": str(row["id"]),
                         "customer_id": str(row["customer_id"]),
                         "lead_id": str(row["lead_id"]) if row["lead_id"] else None})


@bookings_router.patch("/{booking_id}")
async def update_booking_status(booking_id: str, upd: BookingStatusUpdate) -> dict:
    pool = get_pool()
    async with pool.acquire() as conn:
        res = await conn.execute("UPDATE bookings SET status=$1 WHERE id=$2",
                                 upd.status.value, booking_id)
        if res.endswith("0"):
            raise HTTPException(404, "booking not found")
        if upd.status.value == "confirmed":
            await repo.emit_event(conn, "booking_confirmed",
                                  payload={"booking_id": booking_id})
    return {"id": booking_id, "status": upd.status.value}


@jobs_router.post("", status_code=201)
async def create_job(j: JobIn) -> dict:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO jobs (booking_id, customer_id, service_type, amount, notes)
               VALUES ($1,$2,$3,$4,$5) RETURNING id""",
            j.booking_id, j.customer_id, j.service_type, j.amount, j.notes)
        assert row is not None, "job insert returned no row"
    return {"id": str(row["id"])}


@jobs_router.patch("/{job_id}/complete")
async def complete_job(job_id: str, c: JobComplete) -> dict:
    """Mark job complete. Trigger 003 rolls customer LTV; n8n review flow picks it up."""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """UPDATE jobs SET completed_at=COALESCE($2, now()), amount=$3
               WHERE id=$1 RETURNING customer_id""",
            job_id, c.completed_at, c.amount)
        if not row:
            raise HTTPException(404, "job not found")
        await repo.emit_event(conn, "job_completed", customer_id=str(row["customer_id"]),
                              payload={"job_id": job_id, "amount": c.amount})
    return {"id": job_id, "status": "completed"}
