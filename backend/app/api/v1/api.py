from fastapi import APIRouter
from app.api.v1.endpoints import (
    vessels,
    environment,
    icebergs,
    forecasts,
    risk,
    routes,
    alerts,
    navigation,
    jobs,
    ports,
)

api_router = APIRouter()

api_router.include_router(ports.router, prefix="/ports", tags=["ports"])

api_router.include_router(vessels.router, prefix="/vessels", tags=["vessels"])
api_router.include_router(environment.router, prefix="/environment", tags=["environment"])
api_router.include_router(icebergs.router, prefix="/icebergs", tags=["icebergs"])
api_router.include_router(forecasts.router, prefix="/forecasts", tags=["forecasts"])
api_router.include_router(risk.router, prefix="/risk", tags=["risk"])
api_router.include_router(routes.router, prefix="/routes", tags=["routes"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(navigation.router, prefix="/navigation", tags=["navigation"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
