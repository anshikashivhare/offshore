import asyncio
import json
import logging
import time
import uuid

from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)

# API resources that are allowed longer execution time for ML/route workloads.
# Requests are mounted below ``/api/v1``; matching only ``/routes`` previously
# left ``/api/v1/routes/plan`` on the ordinary 15-second deadline.
_SLOW_RESOURCE_SEGMENTS = ("/routes", "/risk", "/predict")


def request_timeout_seconds(path: str) -> float:
    """Choose the deadline from the mounted API path, not an assumed root path."""
    return 60.0 if any(segment in path for segment in _SLOW_RESOURCE_SEGMENTS) else 15.0


class RequestContextMiddleware:
    """Pure ASGI middleware — avoids BaseHTTPMiddleware's streaming-response
    overhead and the per-request asyncio.Task created by wait_for."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        scope.setdefault("state", {})["request_id"] = request_id

        if scope["type"] == "websocket":
            # WebSockets are long-lived — no timeout enforced.
            await self.app(scope, receive, send)
            return

        path: str = scope.get("path", "")
        timeout_seconds = request_timeout_seconds(path)

        start_time = time.perf_counter()
        method = scope.get("method", "")

        status_holder: list = []

        async def send_with_tracking(message):
            if message["type"] == "http.response.start":
                status_holder.append(message.get("status", 0))
                # Inject X-Request-ID into response headers.
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await asyncio.wait_for(
                self.app(scope, receive, send_with_tracking),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            elapsed = time.perf_counter() - start_time
            logger.error(
                "Request timeout (%.1fs) for %s %s [ID: %s]",
                elapsed, method, path, request_id,
            )
            body = json.dumps({
                "error": {
                    "code": "GATEWAY_TIMEOUT",
                    "message": f"Request exceeded the {timeout_seconds:.0f} second limit.",
                    "request_id": request_id,
                }
            }).encode()
            await send({
                "type": "http.response.start",
                "status": 504,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"x-request-id", request_id.encode()),
                ],
            })
            await send({"type": "http.response.body", "body": body})
            return
        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            logger.error(
                "Request failed: %s %s [ID: %s] in %.3fs: %s",
                method, path, request_id, elapsed, exc,
            )
            raise

        elapsed = time.perf_counter() - start_time
        status = status_holder[0] if status_holder else "?"
        logger.info(
            "Request completed: %s %s - Status: %s - Latency: %.3fs - [ID: %s]",
            method, path, status, elapsed, request_id,
        )
