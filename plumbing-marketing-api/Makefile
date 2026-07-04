# Plumbing Marketing API — dev + migration commands.
# Local targets assume DATABASE_URL is set (e.g. via a .env file / your shell).
# Docker targets run against the compose service named `api`.

.DEFAULT_GOAL := help
MSG ?= change me

.PHONY: help install run dev migrate makemigration upgrade downgrade current history dbshell lint \
        docker-migrate docker-dbshell

help:  ## list targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ── local ────────────────────────────────────────────────────────────
install:  ## pip install dependencies
	pip install -r requirements.txt

run:  ## run the app (production-ish)
	uvicorn app.main:app --host 0.0.0.0 --port $${PORT:-8000}

dev:  ## run the app with autoreload
	uvicorn app.main:app --reload --host 0.0.0.0 --port $${PORT:-8000}

migrate: upgrade  ## alias for `upgrade`

upgrade:  ## apply all migrations (alembic upgrade head)
	alembic upgrade head

makemigration:  ## autogenerate a revision: make makemigration MSG="add x"
	alembic revision --autogenerate -m "$(MSG)"

downgrade:  ## roll back one revision
	alembic downgrade -1

current:  ## show the current applied revision
	alembic current

history:  ## show the revision graph
	alembic history --verbose

dbshell:  ## open psql against DATABASE_URL
	psql "$${DATABASE_URL}"

lint:  ## lint (ruff if installed; no-op otherwise)
	@command -v ruff >/dev/null 2>&1 && ruff check app migrations || echo "ruff not installed; skipping"

# ── docker compose ───────────────────────────────────────────────────
docker-migrate:  ## run migrations inside the api container
	docker compose exec api alembic upgrade head

docker-dbshell:  ## psql inside the postgres container
	docker compose exec postgres psql -U plumbing_app -d plumbing_marketing
