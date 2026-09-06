"""
Reliability helpers for ingestion.

These utilities guard against the failure modes documented in the
PHASE 15 brief:

- Missing datasets
- Low-confidence model results
- Unavailable forecast layers
- Failed ingestion
- Unavailable external data sources
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Iterable, Iterator, Optional

logger = logging.getLogger(__name__)


class IngestionFailure(ValueError):
    """Raised when the ingestion pipeline cannot recover from a failure.

    Inherits from ValueError so callers and tests that historically checked
    for ValueError (e.g. validation failures) continue to match.
    """


class DatasetUnavailable(Exception):
    """Raised when an external data source is not reachable."""


def chunked(iterable: Iterable[Any], size: int) -> Iterator[list]:
    """
    Yield successive ``size``-sized chunks from an iterable without loading the
    whole iterable into memory. This is the primary mechanism used to avoid
    materializing large raster datasets in RAM.
    """
    chunk: list = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def safe_call(
    fn: Callable[..., Any],
    *args: Any,
    fallback: Any = None,
    error_code: str = "EXTERNAL_SOURCE_FAILED",
    retryable: bool = True,
    **kwargs: Any,
) -> Any:
    """
    Invoke ``fn`` and translate low-level errors into structured ingestion
    errors so callers can decide whether to retry, skip, or surface the issue.

    The function never re-raises; it always returns either the function's
    return value or ``fallback`` after logging the failure with full context.
    """
    try:
        return fn(*args, **kwargs)
    except Exception as exc:
        logger.error(
            "safe_call[%s] %s failed: %s (retryable=%s)",
            error_code,
            getattr(fn, "__qualname__", repr(fn)),
            exc,
            retryable,
        )
        return fallback


def is_low_confidence(
    confidence: Optional[float],
    threshold: float = 0.5,
) -> bool:
    """Return True if a model result is missing or below the confidence threshold."""
    if confidence is None:
        return True
    try:
        return float(confidence) < threshold
    except (TypeError, ValueError):
        return True


def flag_missing(
    flags: Dict[str, bool], source: str, missing: bool = True
) -> Dict[str, bool]:
    """Append a missing-source flag, useful for accumulating per-source state."""
    flags = dict(flags)
    flags[source] = bool(missing)
    return flags


__all__ = [
    "IngestionFailure",
    "DatasetUnavailable",
    "chunked",
    "safe_call",
    "is_low_confidence",
    "flag_missing",
]
