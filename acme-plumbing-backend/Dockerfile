FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# psql — used by the Render/Railway pre-deploy migration command to apply
# migrations/001_initial_schema.sql idempotently. Small; safe to keep for local too.
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Dependencies first for layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
# Included so the pre-deploy migration command can read the .sql file in-image.
COPY migrations ./migrations

# Bind to the platform-assigned $PORT (Render/Railway inject it); default 8000
# locally so docker-compose keeps working unchanged. Shell form so ${PORT} expands.
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
