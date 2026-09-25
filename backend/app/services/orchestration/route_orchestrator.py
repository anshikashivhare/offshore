import uuid
from typing import Any, Dict, List
from datetime import datetime

from app.schemas.route import RouteRequest, RouteCreate
from app.models.vessel import Vessel
from app.services.routing.astar import AStarRoutePlanner
from app.services.routing.validator import route_validator, RouteValidationError
from app.config.config import settings

class RouteOrchestrator:
    def __init__(self, db_session: Any):
        self.db = db_session
        self.planner = AStarRoutePlanner(resolution=0.5)

    async def execute_route_plan(self, request: RouteRequest, vessel: Vessel) -> RouteCreate:
        demo_mode = getattr(settings, "DEMO_MODE", False)
        
        # 1. Prepare Environmental Context (Sea Ice / Forecast Grid)
        risk_grid = await self._prepare_forecast_context(request)
        
        # 2. Prepare ML Iceberg Context (Candidate Icebergs via spatial bounding)
        candidate_icebergs = await self._prepare_iceberg_context(request, demo_mode)
        
        # 3. Execute Routing (A*)
        try:
            route_create = await self.planner.plan_route(
                request=request,
                vessel=vessel,
                risk_grid=risk_grid,
                demo_mode=demo_mode,
                candidate_icebergs=candidate_icebergs
            )
        except ValueError as exc:
            raise ValueError(f"Routing failed: {exc}")

        # 4. Independent Route Validation
        route_create = self._validate_route(route_create)
        
        # 5. Populate Provenance and ML metadata
        self._populate_metadata(route_create, candidate_icebergs, risk_grid)
        
        return route_create

    async def _prepare_forecast_context(self, request: RouteRequest) -> Any:
        # In a real system, this fetches PostGIS RiskCells via ST_Intersects
        # For now, we return empty dict representing no known risk cells loaded, 
        # allowing fallback to base routing.
        return {}

    async def _prepare_iceberg_context(self, request: RouteRequest, demo_mode: bool) -> List[Dict[str, Any]]:
        # DB-independent candidate fetch
        if demo_mode:
            return [{"iceberg_id": "demo-hazard", "lat": -60.05, "lon": 50.55, "source": "synthetic_demo"}]
        # Production would execute ST_Intersects bounding box query on IcebergDetection here
        return []

    def _validate_route(self, route_create: RouteCreate) -> RouteCreate:
        try:
            is_valid, error_msg, details = route_validator.validate_wkt_linestring(
                route_create.geometry, strict=False
            )
            route_create.land_avoidance_validated = is_valid
            if not is_valid:
                if route_create.warnings is None: route_create.warnings = []
                route_create.warnings.append(f"Route validation failed: {error_msg}")
        except Exception as exc:
            route_create.land_avoidance_validated = False
            if route_create.warnings is None: route_create.warnings = []
            route_create.warnings.append(f"Validation exception: {str(exc)}")
        return route_create

    def _populate_metadata(self, route_create: RouteCreate, icebergs: List[Dict], risk_grid: Any) -> None:
        route_create.candidate_icebergs = len(icebergs)
        if icebergs:
            route_create.iceberg_model_version = "v002"
            route_create.iceberg_forecast_available = True
            route_create.iceberg_risk_status = "active"
            route_create.forecast_coverage_hours = 3.0
        else:
            route_create.iceberg_model_version = "unavailable"
            route_create.iceberg_forecast_available = False
            route_create.iceberg_risk_status = "unavailable"
