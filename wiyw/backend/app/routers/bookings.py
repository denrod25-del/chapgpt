"""Bookings + jobs endpoints (Section 12). Confirmation + review flows hook here."""
import logging
from fastapi import APIRouter, HTTPException
from ..models.db import get_pool
from ..models import repo
from ..services import email, sms
from ..config import config
from .schemas_ext import (BookingIn, BookingStatusUpdate, JobIn, JobComplete)

log = logging.getLogger("wiyw.bookings")
bookings_router = APIRouter(prefix="/bookings", tags=["bookings"])
jobs_router = APIRouter(prefix="/jobs", tags=["jobs"])


@bookings_router.post("", status_code=201)
async def create_booking(b: BookingIn) -> dict:
    """Create booking → Automation #3: confirmation email + SMS."""
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO bookings (customer_id, lead_id, scheduled_for, service_type)
               VALUES ($1,$2,$3,$4) RETURNING id""",
            b.customer_id, b.lead_id, b.scheduled_for, b.service_type)
        assert row, "booking insert returned no row"
        booking_id = str(row["id"])
        cust = await conn.fetchrow(
            "SELECT full_name, phone, email FROM customers WHERE id=$1", b.customer_id)
        if not cust:
            raise HTTPException(404, "customer not found")
        await repo.emit_event(conn, "appointment_booked", customer_id=b.customer_id,
                              payload={"booking_id": booking_id,
                                       "scheduled_for": b.scheduled_for.isoformat()})
        await repo.add_tag(conn, "booked", customer_id=b.customer_id)

    when = b.scheduled_for.strftime("%b %d at %I:%M %p")
    await sms.send_sms(cust["phone"],
                       f"{config.BRAND}: You're booked for {b.service_type.replace('_',' ')} "
                       f"on {when}. Reply C to confirm. Questions? {config.BRAND_PHONE}")
    if cust["email"]:
        await email.send_confirmation(cust["email"], cust["full_name"], b.service_type)
    return {"id": booking_id, "status": "scheduled"}


@bookings_router.patch("/{booking_id}")
async def update_booking_status(booking_id: str, upd: BookingStatusUpdate) -> dict:
    pool = get_pool()
    async with pool.acquire() as conn:
        res = await conn.execute("UPDATE bookings SET status=$1 WHERE id=$2",
                                 upd.status.value, booking_id)
        if res.endswith("0"):
            raise HTTPException(404, "booking not found")
    return {"id": booking_id, "status": upd.status.value}


@jobs_router.post("", status_code=201)
async def create_job(j: JobIn) -> dict:
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO jobs (booking_id, customer_id, service_type, amount, notes)
               VALUES ($1,$2,$3,$4,$5) RETURNING id""",
            j.booking_id, j.customer_id, j.service_type, j.amount, j.notes)
        assert row, "job insert returned no row"
    return {"id": str(row["id"])}


@jobs_router.patch("/{job_id}/complete")
async def complete_job(job_id: str, c: JobComplete) -> dict:
    """Mark job complete. Trigger 003 rolls customer LTV. Review flow (n8n) picks it up."""
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
