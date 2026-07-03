BEGIN;
DROP INDEX IF EXISTS uq_reviews_dedupe;
ALTER TABLE reviews
  DROP COLUMN IF EXISTS dedupe_hash,
  DROP COLUMN IF EXISTS review_date,
  DROP COLUMN IF EXISTS external_source,
  DROP COLUMN IF EXISTS author;
COMMIT;
