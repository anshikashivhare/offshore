import logging
import sys
from typing import Optional

from app.core.config import settings

_CONFIGURED = False


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """
    Configure root logging once for the process.

    - Production / staging: emits JSON-structured logs via python-json-logger.
    - Development / test: emits human-readable logs to stdout.
    """
    global _CONFIGURED
    logger = logging.getLogger()
    log_level = (level or settings.LOG_LEVEL).upper()
    logger.setLevel(log_level)

    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)

    if settings.is_production() or settings.ENVIRONMENT == "staging":
        try:
            from pythonjsonlogger import jsonlogger

            formatter = jsonlogger.JsonFormatter(
                fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%SZ",
            )
        except ImportError:  # pragma: no cover - fallback path
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Re-route uvicorn to use the configured handler.
    for uv_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uv = logging.getLogger(uv_name)
        uv.handlers = [handler]
        uv.propagate = False

    _CONFIGURED = True
    return logging.getLogger(__name__)


logger = setup_logging()
