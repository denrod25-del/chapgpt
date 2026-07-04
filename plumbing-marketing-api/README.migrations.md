# Migrations & DB tooling — Plumbing Marketing API

## What these files are

| File | Purpose |
|---|---|
| `requirements.txt` | deps: FastAPI, SQLAlchemy 2.0, Alembic, asyncpg (app), psycopg (Alembic), pydantic-settings, greenlet |
| `alembic.ini` | Alembic config. **No URL here** — `env.py` loads it from app settings |
| `migrations/env.py` | loads `DATABASE_URL` from `app.core.config`, targets `app.db.base.target_metadata`, runs sync via psycopg |
| `migrations/script.py.mako` | revision template |
| `migrations/versions/0001_initial_schema.py` | first migration: pgcrypto + the 7 tables |
| `app/core/config.py` | pydantic-settings; exposes `async_database_url` (asyncpg) and `alembic_database_url` (psycopg) |
| `app/models/*` | SQLAlchemy 2.0 models; `app/models/base.py` holds `Base` + mixins + naming convention |
| `app/db/base.py` | imports Base + every model so `Base.metadata` is complete (Alembic target) |
| `app/db/session.py` | async engine, `SessionLocal`, `get_db` dependency |
| `app/scripts/prestart.py` | blocks until Postgres answers `SELECT 1`; exits non-zero on failure |
| `docker/app/start.sh` | container entrypoint: prestart → `alembic upgrade head` → uvicorn |
| `Makefile` | `install`, `dev`, `upgrade`, `makemigration`, `downgrade`, `current`, `history`, `dbshell`, … |

## How it fits together

- The **app** runs async on **asyncpg**; **Alembic** runs sync on **psycopg**.
  Both DSNs derive from one `DATABASE_URL`, so there's a single source of truth.
- `env.py` sets `sqlalchemy.url` from `settings.alembic_database_url` at runtime —
  nothing secret lives in `alembic.ini`.
- `target_metadata` comes from `app/db/base.py`, which imports every model, so
  autogenerate sees the whole schema.

## Apply migrations

```bash
export DATABASE_URL=postgresql+asyncpg://plumbing_app:change_me@localhost:5432/plumbing_marketing
alembic upgrade head          # or: make upgrade
alembic current               # confirm you're at 0001
```

## Create a new revision

```bash
# 1. edit models under app/models/
# 2. autogenerate a draft:
make makemigration MSG="add reviews table"     # alembic revision --autogenerate -m ...
# 3. READ migrations/versions/<rev>_add_reviews_table.py, fix anything autogenerate
#    missed (server defaults, partial indexes, data backfills), then:
make upgrade
```

## Docker startup order

`docker/app/start.sh` is the container command:

1. `python -m app.scripts.prestart` — waits for Postgres (30 tries × 2s).
2. `alembic upgrade head` — applies migrations (idempotent; no-op if current).
3. `uvicorn app.main:app` — serves the API on `$PORT` (default 8000).

Point your Dockerfile at it: `CMD ["bash", "docker/app/start.sh"]`
(and `chmod +x docker/app/start.sh`, or invoke via `bash`).

## Common pitfalls

- **Async URL in Alembic.** Alembic can't use `+asyncpg`. `config.alembic_database_url`
  rewrites it to `+psycopg` — keep using that, don't hardcode a URL in `alembic.ini`.
- **Models not imported → empty autogenerate.** Every model must be reachable from
  `app/db/base.py`. Add new model modules to `app/models/__init__.py`.
- **`gen_random_uuid()` missing.** Needs `pgcrypto`; migration 0001 creates the
  extension. Keep that line.
- **Autogenerate over-writes partial indexes / server defaults.** It's a draft —
  always read the generated file before committing.
- **`prestart` uses the async engine.** It needs `asyncpg` + `greenlet` installed
  (both in requirements.txt).

## Local development

```bash
make install                                   # pip install -r requirements.txt
createdb plumbing_marketing                     # + a plumbing_app role, or use your own DSN
export DATABASE_URL=postgresql+asyncpg://<user>:<pw>@localhost:5432/plumbing_marketing
make upgrade                                    # create the schema
make dev                                        # uvicorn --reload
make current history                            # inspect migration state
```
