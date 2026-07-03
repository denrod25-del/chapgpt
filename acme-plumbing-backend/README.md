# Acme Plumbing — Marketing Backend Starter

Minimal production-oriented FastAPI + PostgreSQL foundation for a plumbing brand's
marketing system: lead capture, quote requests (a `lead_type`), booking requests,
event logging, and raw webhook intake. Single brand today (`acme-plumbing` seeded);
every table carries `brand_id` so multi-brand needs no schema change later.

Postgres is the system of record. Brevo (marketing contacts), GatewayAPI (SMS), and
Resend/Mailgun (transactional email) are wired as client stubs to be filled in next.

## Structure

```
migrations/           001_initial_schema.sql — apply with psql (source of truth)
app/
  main.py             FastAPI app, CORS, router mounting
  core/config.py      pydantic-settings Settings (.env driven)
  db/                 base.py (Base + mixins) · session.py (async engine/session)
  models/             SQLAlchemy 2.0 models, one file per table
  schemas/            Pydantic request/response models + enums
  api/                thin route handlers (health, leads, bookings, events, webhooks)
  repositories/       all DB operations (SQL lives here)
  services/           business flows (routes call these; these call repositories)
  integrations/       provider clients (Brevo, GatewayAPI) — transport only
  deps.py             dependency-injected DB session
```

## Run the full stack with Docker Compose (recommended for local dev)

Brings up product Postgres, the migrator, the API, and n8n with one command:

```bash
docker compose up --build
# API      → http://localhost:8000/health
# n8n      → http://localhost:5678
# pgAdmin  → http://localhost:5050
# (optional) cp .env.docker.example .env   # to override ports/secrets
```

Services (`docker-compose.yml`):

| Service | Role | State |
|---|---|---|
| `db` | Postgres 16 — **product data only** | `pgdata` volume |
| `migrate` | applies `001_initial_schema.sql` once, then exits (idempotent) | — |
| `api` | FastAPI backend (system of record) | stateless (Python-stdlib healthcheck) |
| `pgadmin` | web UI for the product DB | `pgadmin_data` volume |
| `n8n` | orchestration layer | **own `n8n_data` volume (SQLite)** |

**pgAdmin:** open http://localhost:5050 (desktop mode — no login prompt). The
product DB is pre-registered as **"Acme Product DB"**; expand it and enter the
password `acme` (the `POSTGRES_PASSWORD` default) on first connect. Override the
pgAdmin login and port via `PGADMIN_DEFAULT_EMAIL` / `PGADMIN_DEFAULT_PASSWORD`
/ `PGADMIN_PORT` in `.env`.

**Why n8n keeps its own volume, not the app's Postgres:** for local dev this
keeps product data and workflow metadata separate and cuts moving parts — n8n
persists its SQLite DB, encryption key, and local files in the `n8n_data`
volume, and the app's Postgres stays focused on leads/bookings/events. n8n is
configured entirely through environment variables in Compose (no bind-mounted
config). To move n8n onto Postgres later, set `DB_TYPE=postgresdb` +
`DB_POSTGRESDB_*` on the `n8n` service — but a **separate database** from the
app's, not shared.

Import the 8 workflows into the running n8n (bulk, via the CLI — the
`n8n/workflows` dir is mounted read-only at `/workflows`):

```bash
docker compose exec n8n n8n import:workflow --separate --input=/workflows
```

or import each file from the n8n UI (**Workflows → Import from File**). Inside
the stack, workflows reach the API at `http://api:8000` (`API_BASE_URL`), which
is preset on the n8n service; `INTERNAL_API_TOKEN` is shared between `api` and
`n8n` so the `Bearer` calls authenticate. All workflows import **inactive**.

Reset everything (including both volumes): `docker compose down -v`.

## Local setup (without Docker)

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

createdb acme_marketing
psql acme_marketing -f migrations/001_initial_schema.sql   # 7 tables + seeded brand

cp .env.example .env    # fill DATABASE_URL at minimum
```

## Run

```bash
uvicorn app.main:app --reload
# GET  http://localhost:8000/health
# POST http://localhost:8000/api/v1/leads
```

Smoke test:

```bash
curl -s -X POST localhost:8000/api/v1/leads -H 'content-type: application/json' -d '{
  "first_name": "Maria", "phone": "+15615550142", "email": "maria@example.com",
  "service_type": "water_heater", "urgency": "standard", "message": "No hot water",
  "page_url": "/water-heaters", "idempotency_key": "demo-001"
}'
```

## Applying the migration

`migrations/001_initial_schema.sql` is a plain SQL file (not Alembic-managed): run it
once against an empty database with `psql`. Future changes should be added as
`002_*.sql`, `003_*.sql` … applied in order — or adopt Alembic and treat 001 as the
baseline revision.

## Next implementation steps (recommended order)

1. **Webhook hardening** — implement the signature verification TODOs in
   `app/services/webhook_service.py` (Mailgun HMAC, Brevo/GatewayAPI shared token)
   and move inbox row processing to a background task that updates
   `processing_status`/`processed_at`.
2. **Comms** — implement `integrations/brevo_client.py` contact sync on lead create,
   and `integrations/gatewayapi_client.py` sends; write every send to
   `communication_logs` and update `delivery_status` from provider webhooks.
3. **Internal auth** — protect non-public routes with `INTERNAL_API_TOKEN`
   (constant-time bearer check dependency).
4. **Booking lifecycle** — PATCH route for status transitions + reminder scan
   (query on `bookings (brand_id, scheduled_for)` is already indexed).
5. **Tests** — pytest against a disposable Postgres: schema validators, contact
   upsert-by-email/phone, lead idempotency replay, webhook dedupe.
