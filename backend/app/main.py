import logging
from contextlib import asynccontextmanager

from app.api.v1.health import router as health_router
from app.config.config import settings
from app.config.exceptions import setup_exception_handlers
from app.config.logging import setup_logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    try:
        settings.validate_for_environment()
    except ValueError as exc:
        logger.critical("Startup validation failed: %s", exc)
        raise

    logger.info("Pre-loading ML models into memory...")
    try:
        from ml.inference.trajectory_predict import load_model as load_trajectory_model
        from ml.inference.seaice_predict import load_model as load_seaice_model
        
        load_trajectory_model()
        load_seaice_model()
        logger.info("ML models successfully loaded.")
    except Exception as exc:
        logger.warning(f"Failed to pre-load ML models (they will load lazily): {exc}")

    logger.info(
        "Starting %s v%s (environment=%s)",
        settings.PROJECT_NAME,
        settings.VERSION,
        settings.ENVIRONMENT,
    )
    logger.info(
        "Configuration: cors_origins=%s db_server=%s redis_uri=%s",
        [str(o) for o in settings.BACKEND_CORS_ORIGINS],
        settings.POSTGRES_SERVER,
        settings.REDIS_URI,
    )
    yield
    logger.info("Shutting down %s", settings.PROJECT_NAME)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url=f"{settings.API_V1_PREFIX}/docs",
        redoc_url=f"{settings.API_V1_PREFIX}/redoc",
        lifespan=lifespan,
    )

    # Restrict CORS via explicit allowlist (never "*").
    if settings.BACKEND_CORS_ORIGINS:
        origins = [str(o) for o in settings.BACKEND_CORS_ORIGINS]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
            allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
            max_age=600,
        )
    else:
        logger.warning(
            "CORS allowlist is empty; cross-origin requests will be blocked."
        )

    if settings.is_production() and settings.TRUST_PROXY_HEADERS:
        # Only enable if explicitly opted-in. Use the configured allowlist, not "*".
        hosts = settings.TRUSTED_HOSTS or ["localhost"]
        if "*" in hosts:
            logger.warning(
                "Refusing to enable TrustedHostMiddleware with wildcard host in production."
            )
        else:
            app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)

    from app.api.middleware import RequestContextMiddleware
    app.add_middleware(RequestContextMiddleware)

    setup_exception_handlers(app)

    # Include routers
    app.include_router(health_router, prefix=settings.API_V1_PREFIX, tags=["health"])
    from app.api.v1.api import api_router

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    from app.ws.routes import router as ws_router

    app.include_router(ws_router, prefix="/ws", tags=["websocket"])

    return app


app = create_app()
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist", "public")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api") or full_path.startswith("ws"):
            raise HTTPException(status_code=404, detail="Not Found")
        return FileResponse(os.path.join(frontend_dist, "index.html"))
