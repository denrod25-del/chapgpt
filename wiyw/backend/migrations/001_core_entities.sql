-- 001_core_entities.sql
-- WiYW marketing/ops schema — customers, leads, bookings, jobs.
-- Idempotent-safe where practical. Apply in numeric order.
-- Rollback: 001_core_entities.down.sql

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ── customers ───────────────────────────────────────────────────────
CREATE TABLE customers (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  full_name      TEXT NOT NULL,
  phone          TEXT NOT NULL UNIQUE,              -- E.164
  email          TEXT,
  address_line   TEXT,
  city           TEXT,
  postal_code    TEXT,
  water_source   TEXT NOT NULL DEFAULT 'unknown'
                   CHECK (water_source IN ('city','well','unknown')),
  lifetime_value NUMERIC(10,2) NOT NULL DEFAULT 0,
  first_job_at   TIMESTAMPTZ,
  last_job_at    TIMESTAMPTZ,
  consent_sms    BOOLEAN NOT NULL DEFAULT false,
  consent_email  BOOLEAN NOT NULL DEFAULT false
);
CREATE INDEX idx_customers_lapsed ON customers (last_job_at);

-- ── leads ───────────────────────────────────────────────────────────
CREATE TABLE leads (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  full_name        TEXT NOT NULL,
  phone            TEXT NOT NULL,
  email            TEXT,
  service_type     TEXT NOT NULL CHECK (service_type IN (
                     'water_treatment','water_softener','whole_house_filter',
                     'ro_system','water_heater','tankless','repipe','drain',
                     'emergency','leak','other')),
  urgency          TEXT NOT NULL DEFAULT 'standard'
                     CHECK (urgency IN ('emergency','standard')),
  water_source     TEXT NOT NULL DEFAULT 'unknown'
                     CHECK (water_source IN ('city','well','unknown')),
  message          TEXT,
  source           TEXT NOT NULL,
  source_medium    TEXT,
  source_campaign  TEXT,
  landing_page     TEXT,
  city             TEXT,
  postal_code      TEXT,
  status           TEXT NOT NULL DEFAULT 'new'
                     CHECK (status IN ('new','contacted','quoted','won','lost')),
  contacted_at     TIMESTAMPTZ,                     -- for missed-lead SLA
  customer_id      UUID REFERENCES customers(id) ON DELETE SET NULL,
  brevo_contact_id TEXT
);
CREATE INDEX idx_leads_status_created ON leads (status, created_at);
CREATE INDEX idx_leads_phone ON leads (phone);
CREATE INDEX idx_leads_missed ON leads (status, created_at) WHERE contacted_at IS NULL;

-- ── bookings ────────────────────────────────────────────────────────
CREATE TABLE bookings (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  customer_id       UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
  lead_id           UUID REFERENCES leads(id) ON DELETE SET NULL,
  scheduled_for     TIMESTAMPTZ NOT NULL,
  service_type      TEXT NOT NULL,
  status            TEXT NOT NULL DEFAULT 'scheduled'
                      CHECK (status IN ('scheduled','confirmed','completed','cancelled','no_show')),
  reminder_24h_sent BOOLEAN NOT NULL DEFAULT false,
  reminder_2h_sent  BOOLEAN NOT NULL DEFAULT false
);
CREATE INDEX idx_bookings_sched ON bookings (scheduled_for, status);
CREATE INDEX idx_bookings_reminder ON bookings (scheduled_for)
  WHERE status IN ('scheduled','confirmed');

-- ── jobs ────────────────────────────────────────────────────────────
CREATE TABLE jobs (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  booking_id       UUID REFERENCES bookings(id) ON DELETE SET NULL,
  customer_id      UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
  completed_at     TIMESTAMPTZ,
  amount           NUMERIC(10,2) CHECK (amount IS NULL OR amount >= 0),
  service_type     TEXT NOT NULL,
  review_requested BOOLEAN NOT NULL DEFAULT false,
  notes            TEXT
);
CREATE INDEX idx_jobs_review_scan ON jobs (completed_at, review_requested)
  WHERE completed_at IS NOT NULL AND review_requested = false;

COMMIT;
