FROM python:3.11-slim AS builder

LABEL org.opencontainers.image.title="SIH-2026 PS-26059 Backend" \
      org.opencontainers.image.description="Antarctic Sea-Ice & Iceberg Navigation API"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    ENVIRONMENT=production

WORKDIR /app

# Runtime system dependencies only (libpq for asyncpg, curl for healthcheck).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove

# Install Python dependencies from the wheel cache built in the previous stage.
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# Copy application source.
COPY app ./app
COPY gunicorn_config.py ./gunicorn_config.py
COPY scripts ./scripts

# Copy the ML inference modules so backend can import ml.inference.*
# Model weights (.json) are excluded from .dockerignore and baked in.
COPY ../ml ./ml

# Non-root user for security.
RUN groupadd --system appgroup \
    && useradd --system --gid appgroup --create-home --home-dir /home/appuser appuser \
    && chown -R appuser:appgroup /app \
    && chmod +x scripts/start.sh

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl --fail --silent http://localhost:8000/api/v1/health || exit 1

CMD ["/app/scripts/start.sh"]
