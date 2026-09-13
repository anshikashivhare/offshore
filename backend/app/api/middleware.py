import asyncio
import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        # We can attach the request_id to the request state
        request.state.request_id = request_id
        
        start_time = time.time()
        
        # Determine dynamic timeout based on path
        path = request.url.path
        timeout_seconds = 15.0  # default
        
        # ML inference and heavy route/risk calculations get 60s
        if "/routes" in path or "/risk" in path or "/predict" in path:
            timeout_seconds = 60.0
            
        is_ws = request.scope.get("type") == "websocket"
            
        try:
            if is_ws:
                # WebSockets are long-lived, do not enforce a timeout
                response = await call_next(request)
            else:
                # We use asyncio.wait_for to enforce the API-level timeout
                response = await asyncio.wait_for(call_next(request), timeout=timeout_seconds)
                response.headers["X-Request-ID"] = request_id
        except asyncio.TimeoutError:
            process_time = time.time() - start_time
            logger.error(f"Request timeout exceeded ({timeout_seconds}s) for {request.method} {path} [ID: {request_id}]")
            return JSONResponse(
                status_code=504,
                content={
                    "error": {
                        "code": "GATEWAY_TIMEOUT",
                        "message": f"Request exceeded the {timeout_seconds} second limit.",
                        "request_id": request_id,
                    }
                },
                headers={"X-Request-ID": request_id}
            )
        except Exception as exc:
            # Let the standard exception handlers handle it, but log here for latency tracking if it failed
            process_time = time.time() - start_time
            logger.error(f"Request failed: {request.method} {path} [ID: {request_id}] in {process_time:.3f}s: {exc}")
            raise
            
        process_time = time.time() - start_time
        status_code = getattr(response, "status_code", "WS")
        logger.info(
            f"Request completed: {request.method} {path} - Status: {status_code} "
            f"- Latency: {process_time:.3f}s - [ID: {request_id}]"
        )
        return response
