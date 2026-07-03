BEGIN;
DROP TRIGGER IF EXISTS trg_job_completed ON jobs;
DROP TRIGGER IF EXISTS trg_leads_touch ON leads;
DROP TRIGGER IF EXISTS trg_customers_touch ON customers;
DROP FUNCTION IF EXISTS on_job_completed();
DROP FUNCTION IF EXISTS touch_updated_at();
COMMIT;
