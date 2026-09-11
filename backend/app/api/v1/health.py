import asyncio
import logging
from typing import Any, Dict

import redis.asyncio as redis
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.config import settings
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    api_status: str
    database_connectivity: str
    redis_connectivity: str
    version: str
    environment: str


async def _check_db(db: AsyncSession) -> str:
    try:
        await asyncio.wait_for(
            db.execute(text("SELECT 1")),
            timeout=settings.EXTERNAL_DATA_TIMEOUT,
        )
        return "ok"
    except Exception as exc:
        logger.error("Database connectivity failed: %s", exc)
        return "failed"


async def _check_redis() -> str:
    client = redis.from_url(settings.REDIS_URI, socket_timeout=2.0)
    try:
        await client.ping()
        return "ok"
    except Exception as exc:
        logger.error("Redis connectivity failed: %s", exc)
        return "failed"
    finally:
        try:
            await client.aclose()
        except Exception:  # pragma: no cover
            pass


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness and dependency health probe",
)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """
    Reports the status of the API process plus connectivity checks for the
    primary database and the Redis broker. Suitable for Kubernetes liveness
    and readiness probes.
    """
    db_status, redis_status = await asyncio.gather(
        _check_db(db), _check_redis(), return_exceptions=False
    )

    api_status = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"

    return HealthResponse(
        api_status=api_status,
        database_connectivity=db_status,
        redis_connectivity=redis_status,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )
