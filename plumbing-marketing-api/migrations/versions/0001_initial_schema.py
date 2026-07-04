"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB
TS = sa.DateTime(timezone=True)


def _id() -> sa.Column:
    return sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"),
                     nullable=False)


def _created() -> sa.Column:
    return sa.Column("created_at", TS, server_default=sa.text("now()"), nullable=False)


def _updated() -> sa.Column:
    return sa.Column("updated_at", TS, server_default=sa.text("now()"), nullable=False)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ── brands ──────────────────────────────────────────────────────
    op.create_table(
        "brands",
        _id(), _created(), _updated(),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("website_domain", sa.Text()),
        sa.Column("primary_city", sa.Text()),
        sa.Column("primary_state", sa.String(length=2)),
        sa.Column("phone", sa.Text()),
        sa.Column("default_from_email", sa.Text()),
        sa.Column("default_from_name", sa.Text()),
        sa.Column("timezone", sa.Text(), server_default=sa.text("'America/New_York'"),
                  nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"),
                  nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_brands"),
        sa.UniqueConstraint("slug", name="uq_brands_slug"),
    )

    # ── contacts ────────────────────────────────────────────────────
    op.create_table(
        "contacts",
        _id(), _created(), _updated(),
        sa.Column("brand_id", UUID, nullable=False),
        sa.Column("first_name", sa.Text(), nullable=False),
        sa.Column("last_name", sa.Text()),
        sa.Column("email", sa.Text()),
        sa.Column("phone", sa.Text()),
        sa.Column("source", sa.Text(), server_default=sa.text("'website'"),
                  nullable=False),
        sa.Column("tags_json", JSONB, server_default=sa.text("'[]'::jsonb"),
                  nullable=False),
        sa.Column("external_refs_json", JSONB, server_default=sa.text("'{}'::jsonb"),
                  nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_contacts"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"],
                                name="fk_contacts_brand_id_brands", ondelete="CASCADE"),
        sa.CheckConstraint("email IS NOT NULL OR phone IS NOT NULL",
                           name="ck_contacts_email_or_phone"),
    )
    op.create_index("ix_contacts_brand_email", "contacts", ["brand_id", "email"],
                    unique=True, postgresql_where=sa.text("email IS NOT NULL"))
    op.create_index("ix_contacts_brand_phone", "contacts", ["brand_id", "phone"],
                    unique=True, postgresql_where=sa.text("phone IS NOT NULL"))

    # ── leads ───────────────────────────────────────────────────────
    op.create_table(
        "leads",
        _id(), _created(), _updated(),
        sa.Column("brand_id", UUID, nullable=False),
        sa.Column("contact_id", UUID),
        sa.Column("lead_type", sa.Text(), server_default=sa.text("'website_form'"),
                  nullable=False),
        sa.Column("source", sa.Text(), server_default=sa.text("'website'"),
                  nullable=False),
        sa.Column("status", sa.Text(), server_default=sa.text("'new'"), nullable=False),
        sa.Column("service_type", sa.Text()),
        sa.Column("urgency", sa.Text(), server_default=sa.text("'standard'"),
                  nullable=False),
        sa.Column("message", sa.Text()),
        sa.Column("page_url", sa.Text()),
        sa.Column("utm_json", JSONB, server_default=sa.text("'{}'::jsonb"),
                  nullable=False),
        sa.Column("meta_json", JSONB, server_default=sa.text("'{}'::jsonb"),
                  nullable=False),
        sa.Column("idempotency_key", sa.Text()),
        sa.PrimaryKeyConstraint("id", name="pk_leads"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"],
                                name="fk_leads_brand_id_brands", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"],
                                name="fk_leads_contact_id_contacts", ondelete="SET NULL"),
    )
    op.create_index("ix_leads_brand_status_created", "leads",
                    ["brand_id", "status", "created_at"])
    op.create_index("ix_leads_contact_id", "leads", ["contact_id"])
    op.create_index("ix_leads_idempotency_key", "leads", ["idempotency_key"],
                    unique=True, postgresql_where=sa.text("idempotency_key IS NOT NULL"))

    # ── bookings ────────────────────────────────────────────────────
    op.create_table(
        "bookings",
        _id(), _created(), _updated(),
        sa.Column("brand_id", UUID, nullable=False),
        sa.Column("contact_id", UUID, nullable=False),
        sa.Column("lead_id", UUID),
        sa.Column("booking_status", sa.Text(), server_default=sa.text("'pending'"),
                  nullable=False),
        sa.Column("scheduled_for", TS, nullable=False),
        sa.Column("timezone", sa.Text(), server_default=sa.text("'America/New_York'"),
                  nullable=False),
        sa.Column("service_address_json", JSONB, server_default=sa.text("'{}'::jsonb"),
                  nullable=False),
        sa.Column("notes", sa.Text()),
        sa.PrimaryKeyConstraint("id", name="pk_bookings"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"],
                                name="fk_bookings_brand_id_brands", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"],
                                name="fk_bookings_contact_id_contacts", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"],
                                name="fk_bookings_lead_id_leads", ondelete="SET NULL"),
    )
    op.create_index("ix_bookings_brand_scheduled", "bookings",
                    ["brand_id", "scheduled_for"])
    op.create_index("ix_bookings_contact_id", "bookings", ["contact_id"])

    # ── event_log (append-only) ─────────────────────────────────────
    op.create_table(
        "event_log",
        _id(), _created(),
        sa.Column("brand_id", UUID, nullable=False),
        sa.Column("contact_id", UUID),
        sa.Column("lead_id", UUID),
        sa.Column("booking_id", UUID),
        sa.Column("event_name", sa.Text(), nullable=False),
        sa.Column("event_source", sa.Text(), server_default=sa.text("'backend'"),
                  nullable=False),
        sa.Column("payload_json", JSONB, server_default=sa.text("'{}'::jsonb"),
                  nullable=False),
        sa.Column("occurred_at", TS, server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_event_log"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"],
                                name="fk_event_log_brand_id_brands", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"],
                                name="fk_event_log_contact_id_contacts", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"],
                                name="fk_event_log_lead_id_leads", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"],
                                name="fk_event_log_booking_id_bookings", ondelete="SET NULL"),
    )
    op.create_index("ix_event_log_brand_name_time", "event_log",
                    ["brand_id", "event_name", "occurred_at"])
    op.create_index("ix_event_log_lead_id", "event_log", ["lead_id"])
    op.create_index("ix_event_log_payload_gin", "event_log", ["payload_json"],
                    postgresql_using="gin")

    # ── communication_logs (append-mostly) ──────────────────────────
    op.create_table(
        "communication_logs",
        _id(), _created(),
        sa.Column("brand_id", UUID, nullable=False),
        sa.Column("contact_id", UUID),
        sa.Column("lead_id", UUID),
        sa.Column("booking_id", UUID),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("direction", sa.Text(), server_default=sa.text("'outbound'"),
                  nullable=False),
        sa.Column("template_key", sa.Text()),
        sa.Column("external_message_id", sa.Text()),
        sa.Column("delivery_status", sa.Text(), server_default=sa.text("'queued'"),
                  nullable=False),
        sa.Column("subject", sa.Text()),
        sa.Column("body_preview", sa.String(length=500)),
        sa.Column("metadata_json", JSONB, server_default=sa.text("'{}'::jsonb"),
                  nullable=False),
        sa.Column("sent_at", TS),
        sa.Column("delivered_at", TS),
        sa.PrimaryKeyConstraint("id", name="pk_communication_logs"),
        sa.ForeignKeyConstraint(["brand_id"], ["brands.id"],
                                name="fk_communication_logs_brand_id_brands",
                                ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"],
                                name="fk_communication_logs_contact_id_contacts",
                                ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"],
                                name="fk_communication_logs_lead_id_leads",
                                ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.id"],
                                name="fk_communication_logs_booking_id_bookings",
                                ondelete="SET NULL"),
    )
    op.create_index("ix_communication_logs_external_message_id", "communication_logs",
                    ["external_message_id"])
    op.create_index("ix_communication_logs_brand_created", "communication_logs",
                    ["brand_id", "created_at"])
    op.create_index("ix_communication_logs_contact_id", "communication_logs",
                    ["contact_id"])

    # ── webhook_inbox (no FKs) ──────────────────────────────────────
    op.create_table(
        "webhook_inbox",
        _id(), _created(),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text()),
        sa.Column("signature", sa.Text()),
        sa.Column("headers_json", JSONB, server_default=sa.text("'{}'::jsonb"),
                  nullable=False),
        sa.Column("payload_json", JSONB, server_default=sa.text("'{}'::jsonb"),
                  nullable=False),
        sa.Column("received_at", TS, server_default=sa.text("now()"), nullable=False),
        sa.Column("processing_status", sa.Text(), server_default=sa.text("'received'"),
                  nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("dedupe_key", sa.Text()),
        sa.Column("processed_at", TS),
        sa.PrimaryKeyConstraint("id", name="pk_webhook_inbox"),
    )
    op.create_index("ix_webhook_inbox_provider_dedupe", "webhook_inbox",
                    ["provider", "dedupe_key"], unique=True,
                    postgresql_where=sa.text("dedupe_key IS NOT NULL"))
    op.create_index("ix_webhook_inbox_pending", "webhook_inbox",
                    ["processing_status", "received_at"],
                    postgresql_where=sa.text("processing_status IN ('received','failed')"))


def downgrade() -> None:
    op.drop_table("webhook_inbox")
    op.drop_table("communication_logs")
    op.drop_table("event_log")
    op.drop_table("bookings")
    op.drop_table("leads")
    op.drop_table("contacts")
    op.drop_table("brands")
    # pgcrypto is left installed — other objects may depend on it.
