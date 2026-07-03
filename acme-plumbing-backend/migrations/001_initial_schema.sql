-- 001_initial_schema.sql — Acme Plumbing marketing backend, first migration.
-- Clean greenfield schema. Apply with:
--   psql "$DATABASE_URL" -f migrations/001_initial_schema.sql

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- gen_random_uuid()

-- Shared updated_at maintenance.
CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS trigger AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ── brands ──────────────────────────────────────────────────────────
-- One row per plumbing brand. Single-brand today; every business table
-- carries brand_id so multi-brand needs no schema change later.
CREATE TABLE brands (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name               TEXT NOT NULL,
  slug               TEXT NOT NULL UNIQUE,
  website_domain     TEXT,
  primary_city       TEXT,
  primary_state      VARCHAR(2),
  phone              TEXT,                          -- E.164
  default_from_email TEXT,
  default_from_name  TEXT,
  is_active          BOOLEAN NOT NULL DEFAULT true,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_brands_touch BEFORE UPDATE ON brands
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- ── contacts ────────────────────────────────────────────────────────
-- People. Leads/bookings hang off a contact; Brevo mirrors this table later
-- (external_refs_json holds provider ids, e.g. {"brevo_contact_id": "123"}).
CREATE TABLE contacts (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id           UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
  first_name         TEXT NOT NULL,
  last_name          TEXT,
  email              TEXT,
  phone              TEXT,                          -- E.164
  source             TEXT NOT NULL DEFAULT 'website',
  tags_json          JSONB NOT NULL DEFAULT '[]',
  external_refs_json JSONB NOT NULL DEFAULT '{}',
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (email IS NOT NULL OR phone IS NOT NULL)
);
-- Upsert identity: email first, then phone (both scoped per brand).
CREATE UNIQUE INDEX uq_contacts_brand_email ON contacts (brand_id, lower(email))
  WHERE email IS NOT NULL;
CREATE UNIQUE INDEX uq_contacts_brand_phone ON contacts (brand_id, phone)
  WHERE phone IS NOT NULL;
CREATE TRIGGER trg_contacts_touch BEFORE UPDATE ON contacts
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- ── leads ───────────────────────────────────────────────────────────
CREATE TABLE leads (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id        UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
  contact_id      UUID REFERENCES contacts(id) ON DELETE SET NULL,
  lead_type       TEXT NOT NULL DEFAULT 'website_form'
                    CHECK (lead_type IN ('website_form','quote_request','phone_call','chat','other')),
  source          TEXT NOT NULL DEFAULT 'website',
  status          TEXT NOT NULL DEFAULT 'new'
                    CHECK (status IN ('new','contacted','quoted','won','lost')),
  service_type    TEXT,                             -- e.g. water_heater, drain, emergency
  urgency         TEXT NOT NULL DEFAULT 'standard'
                    CHECK (urgency IN ('emergency','standard','flexible')),
  message         TEXT,
  page_url        TEXT,
  utm_json        JSONB NOT NULL DEFAULT '{}',
  meta_json       JSONB NOT NULL DEFAULT '{}',
  idempotency_key TEXT,                             -- client-supplied replay guard
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_leads_brand_status_created ON leads (brand_id, status, created_at);
CREATE INDEX idx_leads_contact ON leads (contact_id);
CREATE UNIQUE INDEX uq_leads_idempotency ON leads (idempotency_key)
  WHERE idempotency_key IS NOT NULL;
CREATE TRIGGER trg_leads_touch BEFORE UPDATE ON leads
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- ── bookings ────────────────────────────────────────────────────────
CREATE TABLE bookings (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id             UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
  contact_id           UUID NOT NULL REFERENCES contacts(id) ON DELETE RESTRICT,
  lead_id              UUID REFERENCES leads(id) ON DELETE SET NULL,
  booking_status       TEXT NOT NULL DEFAULT 'pending'
                         CHECK (booking_status IN
                           ('pending','scheduled','confirmed','completed','cancelled','no_show')),
  scheduled_for        TIMESTAMPTZ NOT NULL,
  timezone             TEXT NOT NULL DEFAULT 'America/New_York',
  service_address_json JSONB NOT NULL DEFAULT '{}',
  notes                TEXT,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_bookings_brand_sched ON bookings (brand_id, scheduled_for);
CREATE INDEX idx_bookings_contact ON bookings (contact_id);
CREATE TRIGGER trg_bookings_touch BEFORE UPDATE ON bookings
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- ── event_log ───────────────────────────────────────────────────────
-- Append-only canonical funnel/system log. No updated_at by design.
CREATE TABLE event_log (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id     UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
  contact_id   UUID REFERENCES contacts(id) ON DELETE SET NULL,
  lead_id      UUID REFERENCES leads(id) ON DELETE SET NULL,
  booking_id   UUID REFERENCES bookings(id) ON DELETE SET NULL,
  event_name   TEXT NOT NULL,                       -- snake_case, past tense
  event_source TEXT NOT NULL DEFAULT 'backend',     -- backend | frontend | provider name
  payload_json JSONB NOT NULL DEFAULT '{}',
  occurred_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_event_log_brand_name ON event_log (brand_id, event_name, occurred_at);
CREATE INDEX idx_event_log_lead ON event_log (lead_id);
CREATE INDEX idx_event_log_payload_gin ON event_log USING GIN (payload_json);

-- ── webhook_inbox ───────────────────────────────────────────────────
-- Raw inbound webhook store: insert first, ack fast, process async.
-- (provider, dedupe_key) unique index turns provider re-deliveries into no-ops.
CREATE TABLE webhook_inbox (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider          TEXT NOT NULL
                      CHECK (provider IN ('brevo','mailgun','gatewayapi','other')),
  event_type        TEXT,                           -- provider-native event name
  signature         TEXT,                           -- raw signature header, if any
  headers_json      JSONB NOT NULL DEFAULT '{}',
  payload_json      JSONB NOT NULL DEFAULT '{}',
  received_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  processed_at      TIMESTAMPTZ,
  processing_status TEXT NOT NULL DEFAULT 'received'
                      CHECK (processing_status IN
                        ('received','processing','processed','failed','skipped_duplicate')),
  error_message     TEXT,
  dedupe_key        TEXT                            -- provider event id or body hash
);
CREATE UNIQUE INDEX uq_webhook_inbox_dedupe ON webhook_inbox (provider, dedupe_key)
  WHERE dedupe_key IS NOT NULL;
CREATE INDEX idx_webhook_inbox_pending ON webhook_inbox (processing_status, received_at)
  WHERE processing_status IN ('received','failed');

-- ── communication_logs ──────────────────────────────────────────────
-- One row per message in/out. Delivery webhooks update delivery_status by
-- external_message_id. Append-mostly; no updated_at by design.
CREATE TABLE communication_logs (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id            UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
  contact_id          UUID REFERENCES contacts(id) ON DELETE SET NULL,
  lead_id             UUID REFERENCES leads(id) ON DELETE SET NULL,
  booking_id          UUID REFERENCES bookings(id) ON DELETE SET NULL,
  channel             TEXT NOT NULL CHECK (channel IN ('email','sms')),
  provider            TEXT NOT NULL
                        CHECK (provider IN ('brevo','resend','mailgun','gatewayapi','other')),
  direction           TEXT NOT NULL DEFAULT 'outbound'
                        CHECK (direction IN ('outbound','inbound')),
  template_key        TEXT,                         -- e.g. txn_lead_confirmation, sms_reminder_24h
  external_message_id TEXT,
  delivery_status     TEXT NOT NULL DEFAULT 'queued'
                        CHECK (delivery_status IN ('queued','sent','delivered','failed','bounced')),
  subject             TEXT,
  body_preview        VARCHAR(500),
  metadata_json       JSONB NOT NULL DEFAULT '{}',
  sent_at             TIMESTAMPTZ,
  delivered_at        TIMESTAMPTZ,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_comm_logs_external_id ON communication_logs (external_message_id);
CREATE INDEX idx_comm_logs_brand_created ON communication_logs (brand_id, created_at);
CREATE INDEX idx_comm_logs_contact ON communication_logs (contact_id);

-- ── seed: default brand ─────────────────────────────────────────────
-- Fixed UUID so app code, seeds, and tests can reference it deterministically.
INSERT INTO brands (id, name, slug, website_domain, primary_city, primary_state,
                    default_from_name)
VALUES ('00000000-0000-4000-8000-000000000001', 'Acme Plumbing', 'acme-plumbing',
        'acmeplumbing.example', 'West Palm Beach', 'FL', 'Acme Plumbing');

COMMIT;
