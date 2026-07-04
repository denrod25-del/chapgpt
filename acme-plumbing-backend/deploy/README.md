# Deploying the Acme stack (Render / Railway)

The local `docker-compose.yml` runs everything on one host. In the cloud you
deploy **three independent services** — managed Postgres, the FastAPI API (from
the Dockerfile), and n8n (official image) — and drop pgAdmin (use the platform's
DB console, or connect a local client to the managed DB's external URL).

> **Honest status:** the `render.yaml` blueprint and the steps below are a
> verified-*shape* starting point. They were **not** deployed against a live
> Render/Railway account from this repo, so expect to tweak plan names, regions,
> and hostnames on the first push. The one thing that *is* verified: the
> Dockerfile now binds the platform-injected `$PORT` (tested locally on
> port 10000, still defaults to 8000 for docker-compose).

---

## The one required code change (already applied)

Render/Railway inject a `$PORT` the app must bind to. The Dockerfile CMD is now:

```dockerfile
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

Locally it still defaults to 8000, so `docker compose up` is unchanged.

## The migration decision

The local one-shot `migrate` container isn't reproduced 1:1 in the cloud. Pick one:

1. **One-time, by hand (simplest — start here).** After the DB exists, run the
   schema once from your laptop against the managed DB's external connection URL:
   ```bash
   psql "<EXTERNAL_DATABASE_URL>" -f acme-plumbing-backend/migrations/001_initial_schema.sql
   ```
2. **Automatic pre-deploy (what `render.yaml` is wired for — works out of the box).**
   The API service's `preDeployCommand` applies the schema idempotently before
   each deploy. The Dockerfile already installs `postgresql-client` and copies
   `migrations/` into the image, so no edit is needed — just deploy the Blueprint
   and the migration runs itself (and is a no-op once `brands` exists).

---

## Render (Blueprint)

1. Add the two Dockerfile lines above if you want auto-migration (option 2).
2. In Render: **New → Blueprint**, point it at this repo. Render reads
   `acme-plumbing-backend/render.yaml` and provisions Postgres + `acme-api` +
   `acme-n8n`.
3. Fill the `sync: false` secrets in the dashboard: `RESEND_API_KEY`,
   `BREVO_API_KEY`, `GATEWAYAPI_API_TOKEN`. Leave them blank for a dry run —
   the `/integrations/*` endpoints still return 200 (`sent:false`).
4. If you skipped auto-migration, run option 1 once now.
5. Import the workflows into the deployed n8n (Settings → n8n has no file mount
   in the cloud, so use the UI: **Workflows → Import from File**, upload each JSON
   from `n8n/workflows/`), or via a local CLI pointed at the instance.

Adjust: `plan` values (n8n needs `starter`+ for a disk), the `*.onrender.com`
hostnames in `WEBHOOK_URL` / `N8N_HOST` / `CORS_ORIGINS` / `API_BASE_URL` to
match the names Render assigns.

## Railway (dashboard / CLI)

Railway is less file-driven — wire it in the dashboard:

1. **New Project → Provision PostgreSQL** (exposes a `DATABASE_URL` variable).
2. **New Service → GitHub repo**, set **Root Directory = `acme-plumbing-backend`**
   → it builds the Dockerfile. Add variables:
   - `DATABASE_URL = ${{Postgres.DATABASE_URL}}` (reference variable)
   - `INTERNAL_API_TOKEN = <generate a strong value>`
   - `APP_ENV=production`, `CORS_ORIGINS=<n8n public URL>`, provider keys
   Railway sets `$PORT` automatically; generate a public domain for the service.
3. **New Service → Docker Image `n8nio/n8n:latest`**. Attach a **Volume** mounted
   at `/home/node/.n8n`. Set: `WEBHOOK_URL` + `N8N_HOST` = its public domain,
   `N8N_ENCRYPTION_KEY` = a fixed secret, `API_BASE_URL` = the API service's URL
   (use Railway private networking to keep it internal), the same
   `INTERNAL_API_TOKEN`, plus `DEFAULT_BRAND_SLUG` / `REMINDER_LEAD_HOURS` /
   `REVIEW_REQUEST_DELAY_MINUTES`.
4. Migrate once: `railway run psql $DATABASE_URL -f migrations/001_initial_schema.sql`
   (or the DB console).

---

## Gotchas checklist

| Thing | Why it matters |
|---|---|
| **`$PORT`** | Both platforms assign it; the Dockerfile fix is mandatory or the API is unreachable |
| **n8n persistent disk/volume** | Without it, every redeploy wipes workflows + the encryption key. Mount `/home/node/.n8n` |
| **Fixed `N8N_ENCRYPTION_KEY`** | If it regenerates, saved credentials become unreadable. Set once, keep it |
| **`WEBHOOK_URL` = public n8n URL** | Otherwise n8n hands out unreachable `localhost` webhook URLs |
| **`INTERNAL_API_TOKEN` matches** on API + n8n | It's the bearer the workflows send to `/integrations/*` and `/reviews/request` |
| **Provider keys are secrets** | Set in the dashboard (`sync:false`), never committed |
| **Free tiers sleep / expire** | Fine for a demo; use paid tiers for real traffic. n8n's disk needs a paid Render plan |
| **n8n on Postgres (optional)** | Instead of a disk, set `DB_TYPE=postgresdb` + `DB_POSTGRESDB_*` — but a **separate** database from the app's, never shared |
