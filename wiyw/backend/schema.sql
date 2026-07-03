-- What's in Your Water (WiYW) — marketing/ops schema
-- Palm Beach County | water treatment + full plumbing
-- Tier: NASA-light. All enums CHECK-constrained; FKs enforced; timestamps tz-aware.

CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- gen_random_uuid

-- ── service taxonomy (WiYW-specific) ────────────────────────────────
-- water_treatment | water_softener | whole_house_filter | ro_system
-- water_heater | tankless | repipe | drain | emergency | leak | other

-- ── customers ───────────────────────────────────────────────────────
CREATE TABLE customers (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  full_name      TEXT NOT NULL,
  phone          TEXT NOT NULL UNIQUE,              -- E.164
  email          TEXT,
  address_line   TEXT,
  city           TEXT,
  postal_code    TEXT,
  water_source   TEXT CHECK (water_source IN ('city','well','unknown')) DEFAULT 'unknown',
  lifetime_value NUMERIC(10,2) NOT NULL DEFAULT 0,
  first_job_at   TIMESTAMPTZ,
  last_job_at    TIMESTAMPTZ,
  consent_sms    BOOLEAN NOT NULL DEFAULT false,
  consent_email  BOOLEAN NOT NULL DEFAULT false
);

-- ── leads ───────────────────────────────────────────────────────────
CREATE TABLE leads (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  full_name        TEXT NOT NULL,
  phone            TEXT NOT NULL,                    -- E.164
  email            TEXT,
  service_type     TEXT NOT NULL CHECK (service_type IN (
                     'water_treatment','water_softener','whole_house_filter',
                     'ro_system','water_heater','tankless','repipe','drain',
                     'emergency','leak','other')),
  urgency          TEXT NOT NULL DEFAULT 'standard'
                     CHECK (urgency IN ('emergency','standard')),
  water_source     TEXT CHECK (water_source IN ('city','well','unknown')) DEFAULT 'unknown',
  message          TEXT,
  source           TEXT NOT NULL,                    -- google|direct|meta|referral|...
  source_medium    TEXT,
  source_campaign  TEXT,
  landing_page     TEXT,
  city             TEXT,                             -- PBC city if captured
  postal_code      TEXT,
  status           TEXT NOT NULL DEFAULT 'new'
                     CHECK (status IN ('new','contacted','quoted','won','lost')),
  customer_id      UUID REFERENCES customers(id),
  brevo_contact_id TEXT
);
CREATE INDEX idx_leads_status_created ON leads (status, created_at);
CREATE INDEX idx_leads_phone ON leads (phone);

-- ── bookings ────────────────────────────────────────────────────────
CREATE TABLE bookings (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  customer_id   UUID NOT NULL REFERENCES customers(id),
  lead_id       UUID REFERENCES leads(id),
  scheduled_for TIMESTAMPTZ NOT NULL,
  service_type  TEXT NOT NULL,
  status        TEXT NOT NULL DEFAULT 'scheduled'
                  CHECK (status IN ('scheduled','confirmed','completed','cancelled','no_show')),
  reminder_24h_sent BOOLEAN NOT NULL DEFAULT false,
  reminder_2h_sent  BOOLEAN NOT NULL DEFAULT false
);
CREATE INDEX idx_bookings_sched ON bookings (scheduled_for, status);

-- ── jobs ────────────────────────────────────────────────────────────
CREATE TABLE jobs (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  booking_id       UUID REFERENCES bookings(id),
  customer_id      UUID NOT NULL REFERENCES customers(id),
  completed_at     TIMESTAMPTZ,
  amount           NUMERIC(10,2),
  service_type     TEXT NOT NULL,
  review_requested BOOLEAN NOT NULL DEFAULT false,
  notes            TEXT
);
CREATE INDEX idx_jobs_review_scan ON jobs (completed_at, review_requested);

-- ── reviews ─────────────────────────────────────────────────────────
CREATE TABLE reviews (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  customer_id UUID REFERENCES customers(id),
  job_id      UUID REFERENCES jobs(id),
  rating      INT CHECK (rating BETWEEN 1 AND 5),
  platform    TEXT CHECK (platform IN ('google','facebook','internal')),
  received_at TIMESTAMPTZ,
  content     TEXT
);

-- ── campaigns ───────────────────────────────────────────────────────
CREATE TABLE campaigns (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name       TEXT NOT NULL UNIQUE,   -- <channel>_<purpose>_<city>_<yyyymm>
  channel    TEXT NOT NULL CHECK (channel IN ('email','sms','social','seo')),
  brevo_id   TEXT,
  started_at TIMESTAMPTZ,
  ended_at   TIMESTAMPTZ
);

-- ── events (canonical log) ──────────────────────────────────────────
CREATE TABLE events (
  id            BIGSERIAL PRIMARY KEY,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  event_name    TEXT NOT NULL,
  lead_id       UUID REFERENCES leads(id),
  customer_id   UUID REFERENCES customers(id),
  payload       JSONB NOT NULL DEFAULT '{}',
  source_system TEXT
);
CREATE INDEX idx_events_name_created ON events (event_name, created_at);

-- ── communication_logs ──────────────────────────────────────────────
CREATE TABLE communication_logs (
  id              BIGSERIAL PRIMARY KEY,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  channel         TEXT NOT NULL CHECK (channel IN ('email','sms')),
  direction       TEXT NOT NULL CHECK (direction IN ('outbound','inbound')),
  to_addr         TEXT NOT NULL,
  provider        TEXT NOT NULL CHECK (provider IN ('resend','mailgun','gatewayapi','brevo')),
  provider_msg_id TEXT,
  template        TEXT,
  status          TEXT,
  lead_id         UUID REFERENCES leads(id),
  customer_id     UUID REFERENCES customers(id)
);
CREATE INDEX idx_comms_provider_msg ON communication_logs (provider_msg_id);

-- ── tags / segments ─────────────────────────────────────────────────
CREATE TABLE tags (id SERIAL PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE entity_tags (
  id          BIGSERIAL PRIMARY KEY,
  tag_id      INT NOT NULL REFERENCES tags(id),
  lead_id     UUID REFERENCES leads(id),
  customer_id UUID REFERENCES customers(id),
  applied_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (lead_id IS NOT NULL OR customer_id IS NOT NULL)
);

-- seed tags
INSERT INTO tags (name) VALUES
  ('lead-new'),('quote-pending'),('emergency'),('booked'),
  ('review-requested'),('reactivation'),('well-water'),('city-water')
ON CONFLICT DO NOTHING;

-- ── 005 platform entities (see migrations/005_platform_entities.sql) ─
-- This reference file predates migration 005. The 005 objects — brands (+ brand_id
-- on all core tables), service_areas, campaign_messages, webhooks_inbox,
-- webhook_deliveries, attribution_touches, automation_runs, content_pages,
-- seo_keyword_targets, idempotency_keys, the contacts view, and the expanded
-- 28-name event taxonomy — are defined in the migration, which is canonical.
-- Annotated map: docs/blueprint/03_data_model.md
