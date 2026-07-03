-- Rollback for 005_platform_entities.sql
BEGIN;

DROP VIEW IF EXISTS contacts;

-- Restore the original 002 taxonomy CHECK. NOT VALID: rows written under the
-- expanded taxonomy stay in the log (a rollback must not destroy event history);
-- the constraint still applies to all new inserts.
ALTER TABLE events DROP CONSTRAINT events_event_name_check;
ALTER TABLE events ADD CONSTRAINT events_event_name_check CHECK (event_name IN (
  'landing_page_viewed','service_page_viewed','call_clicked',
  'form_submitted','quote_requested','appointment_booked',
  'appointment_reminder_sent','job_completed','invoice_sent',
  'review_request_sent','review_received','email_opened',
  'email_clicked','sms_clicked')) NOT VALID;

DROP TABLE IF EXISTS idempotency_keys;
DROP TABLE IF EXISTS seo_keyword_targets;
DROP TABLE IF EXISTS content_pages;
DROP TABLE IF EXISTS automation_runs;
DROP TABLE IF EXISTS attribution_touches;
DROP TABLE IF EXISTS webhook_deliveries;
DROP TABLE IF EXISTS webhooks_inbox;
DROP TABLE IF EXISTS campaign_messages;
DROP TABLE IF EXISTS service_areas;

ALTER TABLE customers          DROP COLUMN brand_id;
ALTER TABLE leads              DROP COLUMN brand_id;
ALTER TABLE bookings           DROP COLUMN brand_id;
ALTER TABLE jobs               DROP COLUMN brand_id;
ALTER TABLE reviews            DROP COLUMN brand_id;
ALTER TABLE campaigns          DROP COLUMN brand_id;
ALTER TABLE events             DROP COLUMN brand_id;
ALTER TABLE communication_logs DROP COLUMN brand_id;

DROP TABLE IF EXISTS brands;

COMMIT;
