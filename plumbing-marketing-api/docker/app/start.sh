#!/usr/bin/env bash
# Container entrypoint: wait for DB → run migrations → start the app.
set -euo pipefail

echo "[start] waiting for the database..."
python -m app.scripts.prestart

echo "[start] applying migrations..."
alembic upgrade head

echo "[start] launching uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
