-- 004_reviews_dedup.sql
-- Idempotent Semrush review sync (WF-5): deterministic dedup hash + unique index.
-- Also adds author + external_source for monitoring-fed reviews.
-- Depends on 001,002. Rollback: 004_reviews_dedup.down.sql

BEGIN;

ALTER TABLE reviews
  ADD COLUMN author          TEXT,
  ADD COLUMN external_source TEXT CHECK (external_source IN ('semrush','manual','gbp_direct')),
  ADD COLUMN review_date     DATE;

-- Deterministic hash over the fields that identify a unique review from a monitoring feed.
-- md5 is fine here — collision risk is irrelevant for dedup of human-written reviews.
-- dedupe_hash is computed by the sync layer (n8n WF-5 / backend), NOT a generated column.
-- Rationale: a STORED generated column requires every function in its expression to be
-- IMMUTABLE. Casting int/date to text inside the expression is not guaranteed immutable
-- across settings, so PG rejects it. Computing the hash in the app keeps the schema portable
-- and the hash logic explicit and testable. The DB still enforces uniqueness.
ALTER TABLE reviews ADD COLUMN dedupe_hash TEXT;

-- Backfill any pre-existing rows deterministically (matches the app-side recipe below).
UPDATE reviews SET dedupe_hash = md5(
  coalesce(platform,'') || '|' ||
  coalesce(rating::text,'') || '|' ||
  coalesce(content,'') || '|' ||
  coalesce(to_char(review_date, 'YYYY-MM-DD'),'')
) WHERE dedupe_hash IS NULL;

-- Enforce idempotency: the same review can't land twice.
CREATE UNIQUE INDEX uq_reviews_dedupe ON reviews (dedupe_hash);

-- App/n8n hash recipe (keep identical to the UPDATE above):
--   md5( platform | rating | content | YYYY-MM-DD(review_date) )
-- The one-off UPDATE uses to_char at write time (fine — not a stored generated expr).

COMMIT;
