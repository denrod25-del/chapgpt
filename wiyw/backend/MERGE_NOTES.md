# Merge Notes — verified boot

This is the core wiyw-backend with the Section 12 extensions merged in and boot-tested.

## What was merged
- app/routers/schemas_ext.py   (bookings/jobs/quotes/reviews Pydantic models)
- app/routers/bookings.py       (/bookings + /jobs routers)
- app/routers/quotes_reviews.py (/quotes, /reviews + hardened Mailgun/Brevo webhooks)
- app/main.py                   (registers all new routers)

## Verified against live Postgres (migrations 001-004 applied)
- GET  /health              -> 200
- POST /leads (valid)       -> 201, persisted + event + well-water auto-tag
- POST /leads (bad phone)   -> 422 (E.164 boundary)
- POST /events              -> 201
- POST /quotes              -> 201
- POST /reviews (rating=9)  -> 422 (bounds)
Comms failures with bad keys are handled gracefully (logged, no crash, failover attempted).

## Production DSN note
asyncpg's create_pool takes a standard DSN like:
  postgresql://user:pass@host:5432/wiyw
The test harness used a unix-socket pgserver whose DSN query-string form confused asyncpg's
parser; production TCP DSNs are unaffected. No app code change needed.

## Run migrations in order
psql $DATABASE_URL -f 001_core_entities.sql
psql $DATABASE_URL -f 002_marketing_entities.sql
psql $DATABASE_URL -f 003_triggers.sql
psql $DATABASE_URL -f 004_reviews_dedup.sql
