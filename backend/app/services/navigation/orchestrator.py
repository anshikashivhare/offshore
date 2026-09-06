from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.risk import RiskCell
from app.models.route import Route
from app.models.vessel import Vessel
from app.schemas.alert import AlertCreate, AlertProperties, AlertResponse
from app.schemas.navigation import NavigationScenarioRequest, NavigationScenarioResponse
from app.schemas.route import RouteRequest
from app.services.alerts.engine import AlertEngine
from app.services.routing.astar import AStarRoutePlanner
from app.services.routing.comparison import RouteComparisonService
from app.services.routing.dijkstra import DijkstraShortestPlanner
from app.utils.geojson import parse_wkt_linestring, to_geojson_geometry

logger = logging.getLogger(__name__)


class NavigationOrchestrator:
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.astar = AStarRoutePlanner(resolution=0.5)
        self.shortest = DijkstraShortestPlanner(resolution=0.5)
        self.comparison_service = RouteComparisonService(
            planner=self.astar, shortest_planner=self.shortest
        )
        self.alert_engine = AlertEngine()

    async def _build_environmental_risk_surface(
        self, request: NavigationScenarioRequest
    ) -> Dict[Tuple[float, float], Dict[str, float]]:
        """Fetch the latest persisted risk cells in the route bbox.

        Returns a dict keyed by (lat, lon) rounded to 0.1 degrees, value is a
        dict of per-component risks plus the composite risk.
        """
        if self.db is None:
            return {}
        try:
            origin_lon, origin_lat = (float(x) for x in request.origin.split(","))
            dest_lon, dest_lat = (float(x) for x in request.destination.split(","))
        except (ValueError, AttributeError):
            return {}
        margin = 2.0
        envelope = func.ST_MakeEnvelope(
            min(origin_lon, dest_lon) - margin,
            min(origin_lat, dest_lat) - margin,
            max(origin_lon, dest_lon) + margin,
            max(origin_lat, dest_lat) + margin,
            4326,
        )
        st_intersects = getattr(RiskCell.geometry, "ST_Intersects", None)
        stmt = select(RiskCell)
        if st_intersects is not None:
            stmt = stmt.where(RiskCell.geometry.ST_Intersects(envelope))
        stmt = stmt.order_by(RiskCell.timestamp.desc()).limit(2000)
        rows = (await self.db.execute(stmt)).scalars().all()

        grid: Dict[Tuple[float, float], Dict[str, float]] = {}
        for cell in rows:
            geometry = to_geojson_geometry(cell.geometry)
            if not geometry:
                continue
            if geometry.get("type") == "Polygon":
                ring = geometry["coordinates"][0]
                clat = sum(pt[1] for pt in ring) / len(ring)
                clon = sum(pt[0] for pt in ring) / len(ring)
            elif geometry.get("type") == "Point":
                clon, clat = geometry["coordinates"][0], geometry["coordinates"][1]
            else:
                continue
            key = (round(clat, 1), round(clon, 1))
            existing = grid.get(key)
            if existing is None or cell.composite_risk > existing.get("composite", 0.0):
                grid[key] = {
                    "sea_ice": float(cell.ice_risk),
                    "iceberg": float(cell.iceberg_risk),
                    "weather": float(cell.weather_risk),
                    "current": float(cell.current_risk),
                    "combined": float(cell.composite_risk),
                    "composite": float(cell.composite_risk),
                    "confidence": float(cell.confidence_score or 0.5),
                }
        return grid

    async def run_scenario(
        self, request: NavigationScenarioRequest, vessel: Vessel
    ) -> NavigationScenarioResponse:
        start = time.time()

        risk_grid = await self._build_environmental_risk_surface(request)

        route_req = RouteRequest(
            origin=request.origin,
            destination=request.destination,
            vessel_id=vessel.vessel_id,
            departure_time=request.departure_time,
            objective_type=request.navigation_priority,
            weights=request.custom_weights,
        )

        comparison = await self.comparison_service.compare_routes(
            route_req, vessel, risk_grid
        )
        recommended_route = comparison.recommended_route

        mock_route = Route(
            route_id=recommended_route.properties.route_id,
            vessel_id=vessel.vessel_id,
            origin=recommended_route.properties.origin,
            destination=recommended_route.properties.destination,
            departure_time=recommended_route.properties.departure_time,
            distance=recommended_route.properties.distance,
            eta=recommended_route.properties.eta,
            estimated_fuel=recommended_route.properties.estimated_fuel,
            risk_score=recommended_route.properties.risk_score,
            objective_type=recommended_route.properties.objective_type,
        )
        coords = recommended_route.geometry.coordinates or []
        if coords:
            wkt_pts = ", ".join(f"{pt[0]} {pt[1]}" for pt in coords)
            mock_route.geometry = f"LINESTRING({wkt_pts})"
        else:
            mock_route.geometry = None

        raw_alerts = self.alert_engine.evaluate_route(mock_route, risk_grid)

        # Persist alerts and emit real geometry.
        alerts: List[AlertResponse] = []
        if self.db is not None:
            for raw in raw_alerts:
                try:
                    db_alert = Alert(
                        alert_type=raw.alert_type,
                        severity=raw.severity,
                        location=raw.location,
                        timestamp=raw.timestamp,
                        route_id=raw.route_id,
                        hazard_source=raw.hazard_source,
                        message=raw.message,
                        status=raw.status,
                        triggering_metric=raw.triggering_metric,
                        threshold=raw.threshold,
                        confidence=raw.confidence,
                    )
                    self.db.add(db_alert)
                    await self.db.flush()
                    persisted_id = db_alert.id
                except Exception as exc:
                    logger.warning("Failed to persist alert: %s", exc)
                    persisted_id = uuid.uuid4()
                properties = AlertProperties(
                    id=persisted_id,
                    alert_type=raw.alert_type,
                    severity=raw.severity,
                    timestamp=raw.timestamp,
                    route_id=raw.route_id,
                    hazard_source=raw.hazard_source,
                    message=raw.message,
                    status=raw.status,
                    triggering_metric=raw.triggering_metric,
                    threshold=raw.threshold,
                    confidence=raw.confidence,
                )
                geometry = to_geojson_geometry(raw.location)
                alerts.append(
                    AlertResponse(
                        type="Feature", geometry=geometry, properties=properties
                    )
                )
            try:
                await self.db.commit()
            except Exception as exc:
                logger.warning("Failed to commit alerts: %s", exc)
        else:
            for raw in raw_alerts:
                properties = AlertProperties(
                    id=uuid.uuid4(),
                    alert_type=raw.alert_type,
                    severity=raw.severity,
                    timestamp=raw.timestamp,
                    route_id=raw.route_id,
                    hazard_source=raw.hazard_source,
                    message=raw.message,
                    status=raw.status,
                    triggering_metric=raw.triggering_metric,
                    threshold=raw.threshold,
                    confidence=raw.confidence,
                )
                geometry = to_geojson_geometry(raw.location)
                alerts.append(
                    AlertResponse(
                        type="Feature", geometry=geometry, properties=properties
                    )
                )

        processing_time = time.time() - start
        high_risk_count = sum(
            1 for risks in risk_grid.values() if risks.get("composite", 0) > 0.7
        )

        return NavigationScenarioResponse(
            scenario_metadata={
                "vessel_name": vessel.vessel_name,
                "forecast_horizon": request.forecast_horizon,
                "objective": request.navigation_priority.value,
            },
            recommended_route=recommended_route.model_dump(),
            alternatives=[alt.model_dump() for alt in comparison.alternatives],
            environmental_summary={
                "grid_cells_analyzed": len(risk_grid),
                "high_risk_zones": high_risk_count,
            },
            alerts=alerts,
            explanation=comparison.explanation,
            uncertainty=comparison.uncertainty,
            processing_metadata={
                "processing_time_seconds": round(processing_time, 2),
                "status": "success",
            },
        )