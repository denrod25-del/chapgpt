"""Data-access layer. All SQL lives here; parameterized to prevent injection."""
import json
from typing import Optional

import asyncpg

from ..schemas.leads import LeadIn


async def upsert_lead(conn: asyncpg.Connection, lead: LeadIn) -> str:
    """Insert a lead, returning its UUID. Boundary-validated upstream by Pydantic."""
    row = await conn.fetchrow(
        """
        INSERT INTO leads (full_name, phone, email, service_type, urgency,
                           water_source, message, source, source_medium,
                           source_campaign, landing_page, city, postal_code)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
        RETURNING id, status
        """,
        lead.full_name, lead.phone, lead.email, lead.service_type.value,
        lead.urgency.value, lead.water_source.value, lead.message, lead.source,
        lead.source_medium, lead.source_campaign, lead.landing_page,
        lead.city, lead.postal_code,
    )
    assert row is not None, "insert returned no row"
    return str(row["id"])


async def emit_event(conn: asyncpg.Connection, event_name: str,
                     lead_id: Optional[str] = None,
                     customer_id: Optional[str] = None,
                     payload: Optional[dict] = None,
                     source_system: str = "backend") -> None:
    """Append to the canonical event log (taxonomy CHECK-enforced by the DB)."""
    await conn.execute(
        """
        INSERT INTO events (event_name, lead_id, customer_id, payload, source_system)
        VALUES ($1,$2,$3,$4::jsonb,$5)
        """,
        event_name, lead_id, customer_id, _json(payload or {}), source_system,
    )


async def add_tag(conn: asyncpg.Connection, tag: str,
                  lead_id: Optional[str] = None,
                  customer_id: Optional[str] = None) -> None:
    """Attach a named tag to a lead or customer (tag must be pre-seeded)."""
    await conn.execute(
        """
        INSERT INTO entity_tags (tag_id, lead_id, customer_id)
        SELECT id, $2, $3 FROM tags WHERE name = $1
        ON CONFLICT DO NOTHING
        """,
        tag, lead_id, customer_id,
    )


async def log_comm(conn: asyncpg.Connection, *, channel: str, direction: str,
                   to_addr: str, provider: str, template: str,
                   status: str, provider_msg_id: Optional[str] = None,
                   lead_id: Optional[str] = None,
                   customer_id: Optional[str] = None) -> None:
    await conn.execute(
        """
        INSERT INTO communication_logs
          (channel, direction, to_addr, provider, provider_msg_id, template, status,
           lead_id, customer_id)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
        """,
        channel, direction, to_addr, provider, provider_msg_id, template, status,
        lead_id, customer_id,
    )


async def fetch_booking(conn: asyncpg.Connection, booking_id: str) -> Optional[asyncpg.Record]:
    return await conn.fetchrow(
        """SELECT id, customer_id, lead_id, scheduled_for, service_type, status,
                  reminder_24h_sent, reminder_2h_sent, created_at
           FROM bookings WHERE id=$1""",
        booking_id)


async def claim_review_request(conn: asyncpg.Connection,
                               job_id: str) -> Optional[asyncpg.Record]:
    """Atomically flip jobs.review_requested and return contact info for the sends.
    Returns None when the job doesn't exist OR the request was already claimed —
    callers distinguish via a follow-up existence check."""
    return await conn.fetchrow(
        """UPDATE jobs j SET review_requested=true
           FROM customers c
           WHERE j.id=$1 AND j.review_requested=false AND c.id=j.customer_id
           RETURNING j.id, j.customer_id, c.full_name, c.phone, c.email, c.consent_sms""",
        job_id)


async def dashboard_summary(conn: asyncpg.Connection, brand_id: str,
                            window_days: int) -> dict:
    """Aggregate KPIs for one brand over a trailing window. Read-only."""
    interval = str(window_days)
    leads = await conn.fetchrow(
        """SELECT count(*) AS total,
                  count(*) FILTER (WHERE urgency='emergency' OR service_type='emergency') AS emergency
           FROM leads WHERE brand_id=$1 AND created_at > now() - ($2 || ' days')::interval""",
        brand_id, interval)
    by_source = await conn.fetch(
        """SELECT source, count(*) AS n FROM leads
           WHERE brand_id=$1 AND created_at > now() - ($2 || ' days')::interval
           GROUP BY source ORDER BY n DESC LIMIT 10""",
        brand_id, interval)
    revenue = await conn.fetchrow(
        """SELECT count(*) AS completed_jobs, COALESCE(sum(amount),0) AS total_amount
           FROM jobs WHERE brand_id=$1 AND completed_at > now() - ($2 || ' days')::interval""",
        brand_id, interval)
    reviews = await conn.fetchrow(
        """SELECT count(*) AS received, round(avg(rating)::numeric, 2) AS avg_rating
           FROM reviews WHERE brand_id=$1 AND created_at > now() - ($2 || ' days')::interval""",
        brand_id, interval)
    review_requests = await conn.fetchval(
        """SELECT count(*) FROM events
           WHERE brand_id=$1 AND event_name='review_request_sent'
             AND created_at > now() - ($2 || ' days')::interval""",
        brand_id, interval)
    comms = await conn.fetchrow(
        """SELECT count(*) FILTER (WHERE channel='sms') AS sms_sent,
                  count(*) FILTER (WHERE channel='email') AS email_sent,
                  count(*) FILTER (WHERE status IN ('delivered','sent')) AS ok
           FROM communication_logs
           WHERE brand_id=$1 AND direction='outbound'
             AND created_at > now() - ($2 || ' days')::interval""",
        brand_id, interval)
    runs = await conn.fetchrow(
        """SELECT count(*) AS runs, count(*) FILTER (WHERE status='failed') AS failed
           FROM automation_runs WHERE started_at > now() - ($1 || ' days')::interval""",
        interval)

    total_out = (comms["sms_sent"] or 0) + (comms["email_sent"] or 0)
    return {
        "leads": {"total": leads["total"], "emergency": leads["emergency"],
                  "by_source": {r["source"]: r["n"] for r in by_source}},
        "revenue": {"completed_jobs": revenue["completed_jobs"],
                    "total_amount": float(revenue["total_amount"])},
        "reviews": {"requested": review_requests, "received": reviews["received"],
                    "avg_rating": float(reviews["avg_rating"]) if reviews["avg_rating"] is not None else None},
        "comms": {"sms_sent": comms["sms_sent"], "email_sent": comms["email_sent"],
                  "delivery_rate": round((comms["ok"] or 0) / total_out, 3) if total_out else None},
        "automations": {"runs": runs["runs"], "failed": runs["failed"]},
    }


def _json(d: dict) -> str:
    return json.dumps(d, default=str)
