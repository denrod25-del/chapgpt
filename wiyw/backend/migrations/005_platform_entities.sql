-- 005_platform_entities.sql
-- Platform-layer entities for multi-brand readiness + webhook/idempotency hardening:
--   brands, service_areas, campaign_messages, webhooks_inbox, webhook_deliveries,
--   attribution_touches, automation_runs, content_pages, seo_keyword_targets,
--   idempotency_keys, contacts view, expanded event taxonomy, brand_id on core tables.
-- Depends on 001-003 (touch_updated_at). Rollback: 005_platform_entities.down.sql
-- Single-brand today: every brand_id defaults to the seeded WiYW brand, so existing
-- INSERT paths keep working unchanged.

BEGIN;

-- ── expanded event taxonomy ─────────────────────────────────────────
-- Superset of the 002 CHECK; adds funnel/page + delivery-receipt events.
ALTER TABLE events DROP CONSTRAINT events_event_name_check;
ALTER TABLE events ADD CONSTRAINT events_event_name_check CHECK (event_name IN (
  -- page/funnel (frontend)
  'page_viewed','landing_page_viewed','service_page_viewed',
  'emergency_service_page_viewed','financing_page_viewed','coupon_viewed',
  'call_clicked','form_started','form_submitted',
  -- lead/booking lifecycle (backend)
  'lead_created','quote_requested','booking_requested','appointment_booked',
  'booking_confirmed','appointment_reminder_scheduled','appointment_reminder_sent',
  'job_completed','invoice_sent',
  -- reviews
  'review_request_sent','review_received',
  -- comms delivery/engagement (provider webhooks)
  'email_sent','email_delivered','email_opened','email_clicked',
  'sms_sent','sms_delivered','sms_clicked',
  'contact_unsubscribed'
));


-- ── brands ──────────────────────────────────────────────────────────
-- One row per plumbing brand. WiYW is seeded with a fixed UUID so app code,
-- n8n workflows, and seed scripts can reference it deterministically.
CREATE TABLE brands (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  slug               TEXT NOT NULL UNIQUE,          -- 'wiyw'
  name               TEXT NOT NULL,
  website_domain     TEXT,
  default_from_email TEXT,
  default_from_name  TEXT,
  main_phone         TEXT,                          -- E.164
  booking_url        TEXT,
  gbp_review_url     TEXT,
  timezone           TEXT NOT NULL DEFAULT 'America/New_York',
  is_active          BOOLEAN NOT NULL DEFAULT true
);
CREATE TRIGGER trg_brands_touch BEFORE UPDATE ON brands
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

INSERT INTO brands (id, slug, name, website_domain, default_from_name, timezone)
VALUES ('00000000-0000-4000-8000-000000000001', 'wiyw', 'What''s in Your Water',
        'whatsinyourwater.com', 'What''s in Your Water', 'America/New_York');

-- ── brand_id on core tables ─────────────────────────────────────────
-- Nullable-add → backfill → NOT NULL with DEFAULT keeps 001-004 code paths intact.
ALTER TABLE customers          ADD COLUMN brand_id UUID REFERENCES brands(id);
ALTER TABLE leads              ADD COLUMN brand_id UUID REFERENCES brands(id);
ALTER TABLE bookings           ADD COLUMN brand_id UUID REFERENCES brands(id);
ALTER TABLE jobs               ADD COLUMN brand_id UUID REFERENCES brands(id);
ALTER TABLE reviews            ADD COLUMN brand_id UUID REFERENCES brands(id);
ALTER TABLE campaigns          ADD COLUMN brand_id UUID REFERENCES brands(id);
ALTER TABLE events             ADD COLUMN brand_id UUID REFERENCES brands(id);
ALTER TABLE communication_logs ADD COLUMN brand_id UUID REFERENCES brands(id);

UPDATE customers          SET brand_id = '00000000-0000-4000-8000-000000000001' WHERE brand_id IS NULL;
UPDATE leads              SET brand_id = '00000000-0000-4000-8000-000000000001' WHERE brand_id IS NULL;
UPDATE bookings           SET brand_id = '00000000-0000-4000-8000-000000000001' WHERE brand_id IS NULL;
UPDATE jobs               SET brand_id = '00000000-0000-4000-8000-000000000001' WHERE brand_id IS NULL;
UPDATE reviews            SET brand_id = '00000000-0000-4000-8000-000000000001' WHERE brand_id IS NULL;
UPDATE campaigns          SET brand_id = '00000000-0000-4000-8000-000000000001' WHERE brand_id IS NULL;
UPDATE events             SET brand_id = '00000000-0000-4000-8000-000000000001' WHERE brand_id IS NULL;
UPDATE communication_logs SET brand_id = '00000000-0000-4000-8000-000000000001' WHERE brand_id IS NULL;

ALTER TABLE customers          ALTER COLUMN brand_id SET DEFAULT '00000000-0000-4000-8000-000000000001', ALTER COLUMN brand_id SET NOT NULL;
ALTER TABLE leads              ALTER COLUMN brand_id SET DEFAULT '00000000-0000-4000-8000-000000000001', ALTER COLUMN brand_id SET NOT NULL;
ALTER TABLE bookings           ALTER COLUMN brand_id SET DEFAULT '00000000-0000-4000-8000-000000000001', ALTER COLUMN brand_id SET NOT NULL;
ALTER TABLE jobs               ALTER COLUMN brand_id SET DEFAULT '00000000-0000-4000-8000-000000000001', ALTER COLUMN brand_id SET NOT NULL;
ALTER TABLE reviews            ALTER COLUMN brand_id SET DEFAULT '00000000-0000-4000-8000-000000000001', ALTER COLUMN brand_id SET NOT NULL;
ALTER TABLE campaigns          ALTER COLUMN brand_id SET DEFAULT '00000000-0000-4000-8000-000000000001', ALTER COLUMN brand_id SET NOT NULL;
ALTER TABLE events             ALTER COLUMN brand_id SET DEFAULT '00000000-0000-4000-8000-000000000001', ALTER COLUMN brand_id SET NOT NULL;
ALTER TABLE communication_logs ALTER COLUMN brand_id SET DEFAULT '00000000-0000-4000-8000-000000000001', ALTER COLUMN brand_id SET NOT NULL;

CREATE INDEX idx_leads_brand     ON leads (brand_id, created_at);
CREATE INDEX idx_customers_brand ON customers (brand_id);
CREATE INDEX idx_events_brand    ON events (brand_id, created_at);

-- ── service_areas ───────────────────────────────────────────────────
-- Cities/communities a brand serves. Drives service-area pages + campaign geo codes.
CREATE TABLE service_areas (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  brand_id      UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE
                  DEFAULT '00000000-0000-4000-8000-000000000001',
  name          TEXT NOT NULL,                      -- 'Loxahatchee'
  slug          TEXT NOT NULL,                      -- 'loxahatchee'
  city_code     TEXT NOT NULL,                      -- short code for campaign names: 'lox'
  state         TEXT NOT NULL DEFAULT 'FL',
  postal_codes  TEXT[] NOT NULL DEFAULT '{}',
  water_profile TEXT NOT NULL DEFAULT 'mixed'
                  CHECK (water_profile IN ('city','well','mixed')),
  priority      INT NOT NULL DEFAULT 100,           -- lower = higher SEO priority
  is_active     BOOLEAN NOT NULL DEFAULT true,
  UNIQUE (brand_id, slug)
);
CREATE TRIGGER trg_service_areas_touch BEFORE UPDATE ON service_areas
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- Seed: PBC coverage per docs/KEYWORD_MAP.md. Well-water communities get top priority.
INSERT INTO service_areas (name, slug, city_code, water_profile, priority) VALUES
  ('Loxahatchee',        'loxahatchee',        'lox',     'well',  10),
  ('The Acreage',        'the-acreage',        'acreage', 'well',  10),
  ('Wellington',         'wellington',         'well',    'mixed', 20),
  ('Royal Palm Beach',   'royal-palm-beach',   'rpb',     'mixed', 30),
  ('West Palm Beach',    'west-palm-beach',    'wpb',     'city',  40),
  ('Palm Beach Gardens', 'palm-beach-gardens', 'pbg',     'city',  50),
  ('Jupiter',            'jupiter',            'jupiter', 'city',  50),
  ('Boynton Beach',      'boynton-beach',      'boynton', 'city',  60),
  ('Delray Beach',       'delray-beach',       'delray',  'city',  60),
  ('Boca Raton',         'boca-raton',         'boca',    'city',  60);

-- ── campaign_messages ───────────────────────────────────────────────
-- Individual messages inside a campaign/sequence (mirrors Brevo sequence steps).
CREATE TABLE campaign_messages (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  campaign_id       UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  name              TEXT NOT NULL,
  channel           TEXT NOT NULL CHECK (channel IN ('email','sms')),
  template_key      TEXT NOT NULL,                  -- mkt_/txn_/sms_ template id
  subject           TEXT,
  position          INT NOT NULL DEFAULT 1,         -- step order within the sequence
  send_offset_hours INT,                            -- hours after sequence entry; NULL = one-shot blast
  provider_template_id TEXT,                        -- Brevo template id when mirrored
  UNIQUE (campaign_id, position)
);
CREATE TRIGGER trg_campaign_messages_touch BEFORE UPDATE ON campaign_messages
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- ── webhooks_inbox ──────────────────────────────────────────────────
-- Raw inbound webhook store. INSERT FIRST, return 200 fast, process async.
-- (provider, dedupe_key) unique index makes re-deliveries no-ops.
CREATE TABLE webhooks_inbox (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  received_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  provider        TEXT NOT NULL CHECK (provider IN
                    ('brevo','mailgun','resend','gatewayapi','storyblok','forms','internal','other')),
  event_type      TEXT,                             -- provider-native event name
  dedupe_key      TEXT,                             -- provider msg/event id, or hash of raw body
  signature_valid BOOLEAN,                          -- NULL = provider sends no signature
  headers         JSONB NOT NULL DEFAULT '{}',
  payload         JSONB NOT NULL DEFAULT '{}',      -- parsed body (best-effort)
  raw_body        TEXT,                             -- exact bytes as received
  status          TEXT NOT NULL DEFAULT 'received'
                    CHECK (status IN ('received','processing','processed','failed','skipped_duplicate')),
  attempts        INT NOT NULL DEFAULT 0,
  processed_at    TIMESTAMPTZ,
  error           TEXT
);
CREATE UNIQUE INDEX uq_webhooks_inbox_dedupe ON webhooks_inbox (provider, dedupe_key)
  WHERE dedupe_key IS NOT NULL;
CREATE INDEX idx_webhooks_inbox_pending ON webhooks_inbox (status, received_at)
  WHERE status IN ('received','failed');

-- ── webhook_deliveries ──────────────────────────────────────────────
-- Outbound webhook attempts (backend → n8n etc.) with retry bookkeeping.
CREATE TABLE webhook_deliveries (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  target           TEXT NOT NULL,                   -- logical destination: 'n8n_new_lead'
  url              TEXT NOT NULL,
  event_name       TEXT,                            -- canonical event that triggered it
  payload          JSONB NOT NULL DEFAULT '{}',
  status           TEXT NOT NULL DEFAULT 'pending'
                     CHECK (status IN ('pending','delivered','failed','dead')),
  attempts         INT NOT NULL DEFAULT 0,
  next_attempt_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_status_code INT,
  last_error       TEXT,
  delivered_at     TIMESTAMPTZ
);
CREATE INDEX idx_webhook_deliveries_due ON webhook_deliveries (next_attempt_at)
  WHERE status IN ('pending','failed');

-- ── attribution_touches ─────────────────────────────────────────────
-- Marketing touches per lead/customer (first/last/assist). anonymous_id lets the
-- frontend record touches before a lead identifies itself.
CREATE TABLE attribution_touches (
  id           BIGSERIAL PRIMARY KEY,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  brand_id     UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE
                 DEFAULT '00000000-0000-4000-8000-000000000001',
  lead_id      UUID REFERENCES leads(id) ON DELETE CASCADE,
  customer_id  UUID REFERENCES customers(id) ON DELETE CASCADE,
  anonymous_id TEXT,                                -- frontend cookie id pre-identification
  touch_type   TEXT NOT NULL CHECK (touch_type IN ('first','last','assist')),
  source       TEXT NOT NULL,                       -- google / gbp / direct / social...
  medium       TEXT,                                -- organic / cpc / referral / email / sms
  campaign     TEXT,
  term         TEXT,
  content      TEXT,
  landing_page TEXT,
  referrer     TEXT,
  occurred_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (lead_id IS NOT NULL OR customer_id IS NOT NULL OR anonymous_id IS NOT NULL)
);
CREATE INDEX idx_attr_lead ON attribution_touches (lead_id);
CREATE INDEX idx_attr_anon ON attribution_touches (anonymous_id);

-- ── automation_runs ─────────────────────────────────────────────────
-- One row per n8n/backend automation execution — the ops dashboard for workflows.
CREATE TABLE automation_runs (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  started_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at  TIMESTAMPTZ,
  workflow_key TEXT NOT NULL,                       -- 'wf1_appointment_reminders'
  runner       TEXT NOT NULL DEFAULT 'n8n' CHECK (runner IN ('n8n','backend','brevo')),
  trigger_type TEXT CHECK (trigger_type IN ('schedule','webhook','manual')),
  status       TEXT NOT NULL DEFAULT 'running'
                 CHECK (status IN ('running','success','partial','failed')),
  items_in     INT NOT NULL DEFAULT 0,
  items_out    INT NOT NULL DEFAULT 0,
  items_failed INT NOT NULL DEFAULT 0,
  error        TEXT,
  details      JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_automation_runs_wf ON automation_runs (workflow_key, started_at);

-- ── content_pages ───────────────────────────────────────────────────
-- Mirror of Storyblok stories that matter for SEO ops. Storyblok owns content;
-- this table exists so rank tracking + internal-link audits can join in SQL.
CREATE TABLE content_pages (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  brand_id           UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE
                       DEFAULT '00000000-0000-4000-8000-000000000001',
  storyblok_story_id TEXT,
  slug               TEXT NOT NULL,                 -- 'well-water-treatment'
  title              TEXT,
  page_type          TEXT NOT NULL DEFAULT 'service'
                       CHECK (page_type IN ('homepage','service','service_area','landing','blog','utility')),
  status             TEXT NOT NULL DEFAULT 'draft'
                       CHECK (status IN ('draft','published','archived')),
  published_at       TIMESTAMPTZ,
  meta_title         TEXT,
  meta_description   TEXT,
  target_keyword     TEXT,
  UNIQUE (brand_id, slug)
);
CREATE TRIGGER trg_content_pages_touch BEFORE UPDATE ON content_pages
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- ── seo_keyword_targets ─────────────────────────────────────────────
-- Keyword targets fed by Semrush position tracking / GSC imports.
CREATE TABLE seo_keyword_targets (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  brand_id        UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE
                    DEFAULT '00000000-0000-4000-8000-000000000001',
  keyword         TEXT NOT NULL,
  city            TEXT,                             -- NULL = brand-wide keyword
  intent          TEXT CHECK (intent IN ('emergency','commercial','informational','navigational')),
  target_page_id  UUID REFERENCES content_pages(id) ON DELETE SET NULL,
  priority        INT NOT NULL DEFAULT 100,
  monthly_volume  INT,
  difficulty      INT,
  current_rank    INT,
  best_rank       INT,
  last_checked_at TIMESTAMPTZ,
  source          TEXT NOT NULL DEFAULT 'semrush' CHECK (source IN ('semrush','gsc','manual'))
);
CREATE TRIGGER trg_seo_keyword_targets_touch BEFORE UPDATE ON seo_keyword_targets
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
-- Nullable city needs a coalesce-based uniqueness guard (plain UNIQUE allows dup NULLs).
CREATE UNIQUE INDEX uq_seo_kw ON seo_keyword_targets (brand_id, keyword, COALESCE(city, ''));

-- ── idempotency_keys ────────────────────────────────────────────────
-- Replay guard for retryable POSTs. Client sends Idempotency-Key header; on replay
-- the stored response is returned instead of re-executing side effects.
CREATE TABLE idempotency_keys (
  key             TEXT PRIMARY KEY,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  endpoint        TEXT NOT NULL,
  request_hash    TEXT,                             -- md5 of body; mismatch on replay = 422
  response_status INT,
  response_body   JSONB,
  expires_at      TIMESTAMPTZ NOT NULL DEFAULT now() + interval '48 hours'
);
CREATE INDEX idx_idem_expires ON idempotency_keys (expires_at);

-- ── contacts view ───────────────────────────────────────────────────
-- Unified read model over customers + not-yet-converted leads, keyed by phone.
-- Postgres has no separate contacts table by design: leads/customers ARE the
-- contact records; Brevo mirrors this union.
CREATE VIEW contacts AS
SELECT c.id                AS entity_id,
       'customer'::text    AS entity_type,
       c.brand_id, c.full_name, c.phone, c.email, c.city, c.postal_code,
       c.water_source, c.consent_sms, c.consent_email,
       c.lifetime_value, c.last_job_at, c.created_at
FROM customers c
UNION ALL
SELECT l.id, 'lead', l.brand_id, l.full_name, l.phone, l.email, l.city, l.postal_code,
       l.water_source, false, false, 0::numeric(10,2), NULL::timestamptz, l.created_at
FROM leads l
WHERE l.customer_id IS NULL
  AND l.status NOT IN ('won','lost');

COMMIT;
