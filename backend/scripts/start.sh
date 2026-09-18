#!/bin/sh
set -eu

echo "[start.sh] Running startup validation (Postgres + PostGIS + config)..."
python -m app.startup

# Decide whether to run via Gunicorn (production) or Uvicorn (development)
WORKERS="${UVICORN_WORKERS:-2}"

if [ "${GUNICORN:-false}" = "true" ]; then
    echo "[start.sh] Starting FastAPI via Gunicorn (workers=${WORKERS})..."
    exec gunicorn -c /app/gunicorn_config.py app.main:app
else
    echo "[start.sh] Starting FastAPI via Uvicorn on 0.0.0.0:8000 (workers=${WORKERS})..."
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers "${WORKERS}" \
        --proxy-headers \
        --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-*}" \
        --log-level "${LOG_LEVEL:-info}"
fi


