"""
Startup-time validation.

Run via `python -m app.startup` (or imported by the FastAPI lifespan) to
verify that:

* The application can reach the configured Postgres database.
* The PostGIS extension is available.
* Required environment variables are set (delegated to settings).

Exits with a non-zero status if any check fails, so this can be wired into
container probes or `docker-compose up` health gates.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import List

from app.config.config import settings
from app.db.session import engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


async def _check_postgres() -> List[str]:
    errors: List[str] = []
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            # Verify PostGIS is installed.
            row = (
                await conn.execute(
                    text("SELECT extname FROM pg_extension WHERE extname='postgis'")
                )
            ).first()
            if row is None:
                errors.append(
                    "PostGIS extension is not installed on the configured database. "
                    "Connect as superuser and run: CREATE EXTENSION postgis;"
                )
    except SQLAlchemyError as exc:
        errors.append(f"Database connection failed: {exc}")
    return errors


async def run() -> int:
    try:
        settings.validate_for_environment()
    except ValueError as exc:
        logger.error("Configuration invalid: %s", exc)
        return 1

    errors = await _check_postgres()
    if errors:
        for err in errors:
            logger.error("%s", err)
        return 1

    logger.info(
        "Startup validation succeeded (env=%s, db=%s)",
        settings.ENVIRONMENT,
        settings.POSTGRES_SERVER,
    )
    return 0


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    sys.exit(asyncio.run(run()))


if __name__ == "__main__":
    main()
