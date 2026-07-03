# SECTION 4 — SQL DDL

**The DDL lives in `backend/migrations/` — numbered, transactional, each with a tested
`.down.sql`.** Do not copy DDL from docs; apply the migrations. This page is the map plus the
verification record.

## Apply order

```bash
psql "$DATABASE_URL" -f migrations/001_core_entities.sql       # customers, leads, bookings, jobs
psql "$DATABASE_URL" -f migrations/002_marketing_entities.sql  # reviews, campaigns, events, comm_logs, tags
psql "$DATABASE_URL" -f migrations/003_triggers.sql            # touch_updated_at + LTV rollup
psql "$DATABASE_URL" -f migrations/004_reviews_dedup.sql       # review dedupe hash + author/source
psql "$DATABASE_URL" -f migrations/005_platform_entities.sql   # brands, service_areas, inbox, etc.
```

## What each migration contains

| Migration | Objects |
|---|---|
| 001 | `pgcrypto` extension; **customers, leads, bookings, jobs** + status CHECKs + scan indexes (missed-lead partial, reminder partial, review partial) |
| 002 | **reviews, campaigns, events** (taxonomy CHECK), **communication_logs, tags, entity_tags** (+ partial unique indexes) + 10 seeded tags |
| 003 | `touch_updated_at()` triggers; `on_job_completed()` → rolls `customers.lifetime_value`, `first_job_at`, `last_job_at` |
| 004 | reviews `author`/`external_source`/`review_date`/`dedupe_hash` + `uq_reviews_dedupe` (hash computed app-side — see comment block in the file) |
| 005 | expanded event taxonomy (28 names, replaces the 002 CHECK); **brands** (WiYW seeded, fixed UUID) + `brand_id` on 8 core tables (backfilled, NOT NULL, DEFAULT); **service_areas** (10 PBC cities seeded); **campaign_messages, webhooks_inbox** (+ dedupe unique index), **webhook_deliveries, attribution_touches, automation_runs, content_pages, seo_keyword_targets** (+ COALESCE unique index), **idempotency_keys**; `contacts` view |

`backend/schema.sql` is the human-readable consolidated reference; regenerate or extend it when
migrations change — migrations always win on conflict.

## Non-obvious DDL decisions (read before editing)

1. **005 alters the events CHECK *first*, before any UPDATE on `events`** — an UPDATE re-checks
   constraints, so backfilling `brand_id` under the old CHECK would fail once new-taxonomy rows
   exist. Order matters; keep it.
2. **005.down re-adds the old taxonomy CHECK as `NOT VALID`** — a rollback must not require
   destroying event-log rows written under the expanded taxonomy. New inserts are still checked.
3. **`dedupe_hash` is not a generated column** — Postgres rejects non-IMMUTABLE generated
   expressions (int/date→text casts). App/n8n computes it; the DB enforces uniqueness.
4. **TEXT + CHECK instead of ENUM types** — adding a status is a constraint swap inside one
   transaction, not an `ALTER TYPE` dance.
5. **Fixed brand UUID** `00000000-0000-4000-8000-000000000001` as column DEFAULT — the
   single-brand app code never mentions brands; multi-brand later = drop the DEFAULT and pass
   `brand_id` explicitly.

## Verification record (this session, Postgres 16.13)

- 001→005 apply clean on a fresh DB (`ON_ERROR_STOP=1`).
- 005 up → down → up cycle passes; down preserves event rows (NOT VALID restore).
- `webhooks_inbox` dedupe: duplicate `(provider, dedupe_key)` insert rejected.
- Legacy insert paths unaffected: `POST /leads` on the booted backend persists with
  auto-filled `brand_id` + auto-tags (`lead-new`, `well-water`); new taxonomy name
  `page_viewed` accepted via `POST /events`; old CHECKs (`service_type`, rating bounds) still
  enforce.
- `contacts` view returns the unconverted lead as `entity_type='lead'`.
