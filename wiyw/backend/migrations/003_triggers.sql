-- 003_triggers.sql
-- Auto-maintain updated_at; roll customer LTV + last_job_at on job completion.
-- Depends on 001,002. Rollback: 003_triggers.down.sql

BEGIN;

CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at := now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_customers_touch BEFORE UPDATE ON customers
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();
CREATE TRIGGER trg_leads_touch BEFORE UPDATE ON leads
  FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

-- When a job is completed, advance customer LTV + job timestamps.
CREATE OR REPLACE FUNCTION on_job_completed() RETURNS TRIGGER AS $$
BEGIN
  IF NEW.completed_at IS NOT NULL
     AND (OLD.completed_at IS NULL OR OLD.completed_at <> NEW.completed_at) THEN
    UPDATE customers
       SET lifetime_value = lifetime_value + COALESCE(NEW.amount, 0),
           last_job_at    = NEW.completed_at,
           first_job_at   = COALESCE(first_job_at, NEW.completed_at)
     WHERE id = NEW.customer_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_job_completed AFTER UPDATE ON jobs
  FOR EACH ROW EXECUTE FUNCTION on_job_completed();

COMMIT;
