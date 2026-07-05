-- 002_review_requests_and_webhook_reconciliation.sql
-- Adds review-request scheduling + widens webhook/communication schema for
-- delivery reconciliation. Apply after 001. Idempotent where practical.
--
--   psql "$DATABASE_URL" -f migrations/002_review_requests_and_webhook_reconciliation.sql
--
-- NOTE: this project applies plain-SQL migrations via psql (see Dockerfile /
-- docker-compose 'migrate' service). The task requested an Alembic file under
-- migrations/versions/; that would be dead code here since there is no Alembic
-- runtime in this service, so the change is delivered as SQL to stay runnable.

BEGIN;

-- ── webhook_inbox: verification result + created_at ──────────────────────────
ALTER TABLE webhook_inbox
  ADD COLUMN IF NOT EXISTS verification_status TEXT NOT NULL DEFAULT 'pending';
ALTER TABLE webhook_inbox
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE webhook_inbox DROP CONSTRAINT IF EXISTS ck_webhook_inbox_verification;
ALTER TABLE webhook_inbox ADD CONSTRAINT ck_webhook_inbox_verification
  CHECK (verification_status IN
    ('pending','verified','unverified','invalid','unconfigured'));

-- ── communication_logs: widen delivery_status vocabulary ────────────────────
-- 001 created an inline (auto-named) CHECK limited to
-- queued/sent/delivered/failed/bounced. Reconciliation needs the fuller set.
ALTER TABLE communication_logs
  DROP CONSTRAINT IF EXISTS communication_logs_delivery_status_check;
ALTER TABLE communication_logs
  DROP CONSTRAINT IF EXISTS ck_communication_logs_delivery_status;
ALTER TABLE communication_logs ADD CONSTRAINT ck_communication_logs_delivery_status
  CHECK (delivery_status IN (
    'queued','sent','delivered','opened','clicked','deferred',
    'soft_bounce','blocked','hard_bounce','failed','bounced',
    'complaint','unsubscribed'
  ));

-- ── review_requests ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS review_requests (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id             UUID NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
  contact_id           UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
  lead_id              UUID REFERENCES leads(id) ON DELETE SET NULL,
  booking_id           UUID REFERENCES bookings(id) ON DELETE SET NULL,
  communication_log_id UUID REFERENCES communication_logs(id) ON DELETE SET NULL,
  channel              TEXT NOT NULL CHECK (channel IN ('email','sms')),
  status               TEXT NOT NULL DEFAULT 'pending'
                         CHECK (status IN
                           ('pending','due','sent','delivered','clicked',
                            'completed','failed','canceled')),
  review_url           TEXT NOT NULL,
  scheduled_for        TIMESTAMPTZ NOT NULL,
  sent_at              TIMESTAMPTZ,
  completed_at         TIMESTAMPTZ,
  failure_reason       TEXT,
  metadata_json        JSONB NOT NULL DEFAULT '{}',
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- "What's due now" poller scan (partial: only actionable rows).
CREATE INDEX IF NOT EXISTS idx_review_requests_due
  ON review_requests (status, scheduled_for)
  WHERE status IN ('pending','due');
CREATE INDEX IF NOT EXISTS idx_review_requests_brand
  ON review_requests (brand_id, created_at);
CREATE INDEX IF NOT EXISTS idx_review_requests_contact
  ON review_requests (contact_id);

-- Postgres has no CREATE TRIGGER IF NOT EXISTS; drop-then-create to stay re-runnable.
DROP TRIGGER IF EXISTS trg_review_requests_touch ON review_requests;
CREATE TRIGGER trg_review_requests_touch BEFORE UPDATE ON review_requests
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

COMMIT;
