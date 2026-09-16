import os
import json
import inspect
from functools import wraps
from typing import Callable, Any

from fastapi import Request, Depends
from fastapi.responses import JSONResponse

# Optional Redis backend – use if REDIS_URL env var is set
REDIS_URL = os.getenv("REDIS_URL")

if REDIS_URL:
    try:
        import redis.asyncio as redis
        _redis_client = redis.from_url(REDIS_URL)
    except Exception:  # pragma: no cover
        _redis_client = None
else:
    _redis_client = None

# Simple in‑memory cache for development / testing
_memory_cache: dict[str, Any] = {}


def _cache_key(request: Request) -> str:
    """Generate a deterministic cache key based on HTTP method, path, and sorted query parameters."""
    params = "&".join(f"{k}={v}" for k, v in sorted(request.query_params.items()))
    return f"{request.method}:{request.url.path}?{params}"


def cache_response(ttl: int = 300) -> Callable[[Callable], Callable]:
    """FastAPI decorator to cache JSON responses.

    Args:
        ttl: Time‑to‑live in seconds (default 5 minutes).
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, request: Request = Depends(), **kwargs):
            key = _cache_key(request)
            # Try Redis first
            if _redis_client:
                cached_bytes = await _redis_client.get(key)
                if cached_bytes is not None:
                    cached = json.loads(cached_bytes.decode())
                    return JSONResponse(content=cached)
            else:
                cached = _memory_cache.get(key)
                if cached is not None:
                    return JSONResponse(content=cached)

            # Call original endpoint, handling sync vs async
            if inspect.iscoroutinefunction(func):
                response = await func(*args, request=request, **kwargs)
            else:
                response = func(*args, request=request, **kwargs)

            payload = response if isinstance(response, dict) else response.body
            if _redis_client:
                # Serialize payload to JSON string before storing
                await _redis_client.set(key, json.dumps(payload), ex=ttl)
            else:
                _memory_cache[key] = payload
            return response
        return wrapper
    return decorator

# ---------------------------------------------------------------------------
# Cache invalidation helpers (to be called after mutating data)
# ---------------------------------------------------------------------------

import asyncio

async def _invalidate_redis_keys(pattern: str) -> None:
    """Delete Redis keys matching a glob pattern (async)."""
    if not _redis_client:
        return
    keys = await _redis_client.keys(pattern)
    if keys:
        await _redis_client.delete(*keys)

def clear_cache_for_prefix(prefix: str) -> None:
    """Clear both in‑memory and Redis caches for keys that start with *prefix*.

    *prefix* should be the request path, e.g. ``/api/v1/ports``.
    """
    # In‑memory clear
    to_delete = [k for k in list(_memory_cache) if k.startswith(prefix)]
    for k in to_delete:
        _memory_cache.pop(k, None)
    # Redis clear (fire‑and‑forget async task)
    asyncio.create_task(_invalidate_redis_keys(f"*{prefix}*"))
