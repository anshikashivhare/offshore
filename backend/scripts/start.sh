#!/bin/sh
set -eu

echo "[start.sh] Running Alembic database migrations..."
alembic upgrade head

echo "[start.sh] Running startup validation (Postgres + PostGIS + config)..."
python -m app.startup

echo "[start.sh] Starting FastAPI (uvicorn) on 0.0.0.0:8000 with ${UVICORN_WORKERS:-2} workers..."
WORKERS="${UVICORN_WORKERS:-2}"
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${WORKERS}" \
    --proxy-headers \
    --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-*}" \
    --log-level "${LOG_LEVEL:-info}"
