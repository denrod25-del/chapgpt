-- 002_marketing_entities.sql
-- reviews, campaigns, events (taxonomy), communication_logs, tags/segments.
-- Depends on 001. Rollback: 002_marketing_entities.down.sql

BEGIN;

-- ── reviews ─────────────────────────────────────────────────────────
CREATE TABLE reviews (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
  job_id      UUID REFERENCES jobs(id) ON DELETE SET NULL,
  rating      INT CHECK (rating BETWEEN 1 AND 5),
  platform    TEXT CHECK (platform IN ('google','facebook','internal')),
  received_at TIMESTAMPTZ,
  content     TEXT
);

-- ── campaigns ───────────────────────────────────────────────────────
CREATE TABLE campaigns (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  name       TEXT NOT NULL UNIQUE,   -- <channel>_<purpose>_<city>_<yyyymm>
  channel    TEXT NOT NULL CHECK (channel IN ('email','sms','social','seo')),
  brevo_id   TEXT,
  started_at TIMESTAMPTZ,
  ended_at   TIMESTAMPTZ
);

-- ── events (canonical log; SECTION 4 taxonomy enforced) ─────────────
CREATE TABLE events (
  id            BIGSERIAL PRIMARY KEY,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  event_name    TEXT NOT NULL CHECK (event_name IN (
                  'landing_page_viewed','service_page_viewed','call_clicked',
                  'form_submitted','quote_requested','appointment_booked',
                  'appointment_reminder_sent','job_completed','invoice_sent',
                  'review_request_sent','review_received','email_opened',
                  'email_clicked','sms_clicked')),
  lead_id       UUID REFERENCES leads(id) ON DELETE SET NULL,
  customer_id   UUID REFERENCES customers(id) ON DELETE SET NULL,
  payload       JSONB NOT NULL DEFAULT '{}',
  source_system TEXT NOT NULL DEFAULT 'backend'
);
CREATE INDEX idx_events_name_created ON events (event_name, created_at);
CREATE INDEX idx_events_lead ON events (lead_id);
CREATE INDEX idx_events_payload_gin ON events USING GIN (payload);

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
  lead_id         UUID REFERENCES leads(id) ON DELETE SET NULL,
  customer_id     UUID REFERENCES customers(id) ON DELETE SET NULL
);
CREATE INDEX idx_comms_provider_msg ON communication_logs (provider_msg_id);
CREATE INDEX idx_comms_customer ON communication_logs (customer_id, created_at);

-- ── tags / segments ─────────────────────────────────────────────────
CREATE TABLE tags (
  id   SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL
);
CREATE TABLE entity_tags (
  id          BIGSERIAL PRIMARY KEY,
  tag_id      INT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  lead_id     UUID REFERENCES leads(id) ON DELETE CASCADE,
  customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
  applied_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (lead_id IS NOT NULL OR customer_id IS NOT NULL)
);
CREATE UNIQUE INDEX uq_entity_tag_lead ON entity_tags (tag_id, lead_id)
  WHERE lead_id IS NOT NULL;
CREATE UNIQUE INDEX uq_entity_tag_cust ON entity_tags (tag_id, customer_id)
  WHERE customer_id IS NOT NULL;

INSERT INTO tags (name) VALUES
  ('lead-new'),('quote-pending'),('emergency'),('booked'),
  ('review-requested'),('reactivation'),('reactivation-warm'),
  ('well-water'),('city-water'),('high-value')
ON CONFLICT DO NOTHING;

COMMIT;
