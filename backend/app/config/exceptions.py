import logging
import uuid
from typing import Any, Dict, Optional

from app.config.config import settings
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Domain-level error carrying an HTTP status and machine-readable code."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        code: str = "APP_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}


def _error_payload(
    code: str,
    message: str,
    details: Optional[Any] = None,
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    if trace_id is not None:
        payload["error"]["trace_id"] = trace_id
    return payload


def setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        trace_id = getattr(request.state, "request_id", None)
        logger.warning(
            "AppError at %s [%s]: %s [ID: %s]",
            request.url.path,
            exc.code,
            exc.message,
            trace_id,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(exc.code, exc.message, exc.details or None, trace_id=trace_id),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        trace_id = getattr(request.state, "request_id", None)
        logger.info(
            "Validation error at %s: %s [ID: %s]",
            request.url.path,
            exc.errors(),
            trace_id,
        )
        safe_errors = []
        for err in exc.errors():
            safe_err = {k: v for k, v in err.items() if k not in ("ctx",)}
            safe_errors.append(safe_err)

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_payload(
                code="VALIDATION_ERROR",
                message="Invalid request payload",
                details=safe_errors,
                trace_id=trace_id,
            ),
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        trace_id = getattr(request.state, "request_id", uuid.uuid4().hex)
        # Always log the full traceback server-side, never expose it to the client.
        logger.exception(
            "Unhandled exception at %s [trace_id=%s]",
            request.url.path,
            trace_id,
        )
        detail = "Internal server error"
        if not settings.is_production():
            detail = f"{type(exc).__name__}: {exc}"

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_payload(
                code="INTERNAL_SERVER_ERROR",
                message=detail,
                trace_id=trace_id if settings.is_production() else None,
            ),
        )
