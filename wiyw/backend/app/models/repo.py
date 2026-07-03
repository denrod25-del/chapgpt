"""Data-access layer. All SQL lives here; parameterized to prevent injection."""
from typing import Optional
import asyncpg
from .schemas import LeadIn


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
    """Append to the canonical event log."""
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
        """,
        tag, lead_id, customer_id,
    )


async def log_comm(conn: asyncpg.Connection, *, channel: str, direction: str,
                   to_addr: str, provider: str, template: str,
                   status: str, provider_msg_id: Optional[str] = None,
                   lead_id: Optional[str] = None) -> None:
    await conn.execute(
        """
        INSERT INTO communication_logs
          (channel, direction, to_addr, provider, provider_msg_id, template, status, lead_id)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
        """,
        channel, direction, to_addr, provider, provider_msg_id, template, status, lead_id,
    )


def _json(d: dict) -> str:
    import json
    return json.dumps(d, default=str)
