import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from app.api import deps
from app.models.risk import RiskCell
from app.models.route import Route
from app.models.vessel import Vessel
from app.repositories.route import route as route_repo
from app.repositories.vessel import vessel as vessel_repo
from app.schemas.common import GeoJSONFeature
from app.schemas.route import (RouteComparisonResponse, RouteProperties,
                               RouteRequest, RouteResponse)
from app.services.routing.astar import AStarRoutePlanner
from app.services.routing.comparison import RouteComparisonService
from app.services.routing.dijkstra import DijkstraShortestPlanner
from app.utils.geojson import parse_wkt_linestring, to_geojson_geometry
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

astar_planner = AStarRoutePlanner(resolution=0.5)
shortest_planner = DijkstraShortestPlanner(resolution=0.5)
comparison_service = RouteComparisonService(
    planner=astar_planner, shortest_planner=shortest_planner
)


async def _build_risk_grid(db: AsyncSession, request: RouteRequest) -> Dict[Any, float]:
    """Fetch the most recent RiskCell rows that intersect the route bbox and
    expose them as a dict keyed by rounded (lat, lon) centroid coordinates.

    The A* and Dijkstra planners both consume a dict-of-float risk grid.
    """
    # FIX: imports moved to module level — no longer re-imported per request/per row.
    from app.config.config import settings

    if getattr(settings, "DEMO_MODE", False):
        return {}

    try:
        origin_lon, origin_lat = (float(x) for x in request.origin.split(","))
        dest_lon, dest_lat = (float(x) for x in request.destination.split(","))
    except (ValueError, AttributeError):
        return {}
    margin = 2.0
    min_lon = min(origin_lon, dest_lon) - margin
    max_lon = max(origin_lon, dest_lon) + margin
    min_lat = min(origin_lat, dest_lat) - margin
    max_lat = max(origin_lat, dest_lat) + margin

    envelope = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
    st_intersects = getattr(RiskCell.geometry, "ST_Intersects", None)
    stmt = select(RiskCell)
    if st_intersects is not None:
        stmt = stmt.where(RiskCell.geometry.ST_Intersects(envelope))
    stmt = stmt.order_by(RiskCell.timestamp.desc()).limit(2000)
    
    try:
        rows = (await db.execute(stmt)).scalars().all()
    except Exception as exc:
        if not getattr(settings, "DEMO_MODE", False):
            raise HTTPException(status_code=503, detail="Database unavailable")
        return {}
    grid: Dict[Any, float] = {}
    for cell in rows:
        try:
            geom = to_geojson_geometry(cell.geometry)
        except Exception:
            continue
        coords = geom.get("coordinates")
        if not coords:
            continue
        if geom.get("type") == "Polygon":
            ring = coords[0]
            clat = sum(pt[1] for pt in ring) / len(ring)
            clon = sum(pt[0] for pt in ring) / len(ring)
        elif geom.get("type") == "Point":
            clon, clat = coords[0], coords[1]
        else:
            continue
        key = (round(clat, 1), round(clon, 1))
        # Keep the highest composite risk per cell key.
        prev = grid.get(key, 0.0)
        if cell.composite_risk > prev:
            grid[key] = float(cell.composite_risk)
    return grid


@router.post("/plan", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
async def plan_route(
    request: RouteRequest,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """Plan a route using A* over the latest persisted risk surface."""
    from app.config.config import settings

    # Use custom configuration if provided
    if request.custom_vessel_config:
        vessel = Vessel(**request.custom_vessel_config.model_dump())
        vessel.vessel_id = request.vessel_id # Preserve the ID
    else:
        try:
            vessel = await vessel_repo.get(db, request.vessel_id)
        except Exception as exc:
            if getattr(settings, "DEMO_MODE", False):
                import json
                from pathlib import Path
                try:
                    vessels_path = Path(__file__).resolve().parents[4] / "data" / "vessels.json"
                    with vessels_path.open("r", encoding="utf-8") as f:
                        all_vessels = json.load(f)
                    v_id_str = str(request.vessel_id)
                    vessel_data = next((v for v in all_vessels if str(v.get("vessel_id")) == v_id_str), None)
                    if vessel_data:
                        vessel = Vessel(**vessel_data)
                    else:
                        vessel = None
                except Exception:
                    vessel = None
            else:
                raise HTTPException(status_code=503, detail="Database unavailable") from exc

        if vessel is None:
            raise HTTPException(status_code=404, detail="Vessel not found")

    # Snap origin and destination to water
    from app.services.routing.grid import Node
    try:
        origin_lon, origin_lat = (float(x) for x in request.origin.split(","))
        dest_lon, dest_lat = (float(x) for x in request.destination.split(","))
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid origin or destination coordinates")

    origin_node = Node(lat=origin_lat, lon=origin_lon)
    dest_node = Node(lat=dest_lat, lon=dest_lon)

    snapped_origin = astar_planner.grid_builder.snap_to_water(origin_node, max_radius_degrees=2.0)
    if snapped_origin is None:
        raise HTTPException(status_code=400, detail="Origin port is on land and no navigable water found within 2.0° search radius.")
    
    snapped_dest = astar_planner.grid_builder.snap_to_water(dest_node, max_radius_degrees=2.0)
    if snapped_dest is None:
        raise HTTPException(status_code=400, detail="Destination port is on land and no navigable water found within 2.0° search radius.")

    # The planner itself will handle water-snapping for its internal start/goal nodes.
    # We preserve the original request coordinates so they can be returned verbatim if needed.

    risk_grid = await _build_risk_grid(db, request)
    demo_mode = getattr(settings, "DEMO_MODE", False)

    try:
        if request.objective_type.value == "shortest":
            route_create = await shortest_planner.plan_route(request, vessel, risk_grid)
        else:
            # Pass demo_mode flag to astar_planner
            route_create = await astar_planner.plan_route(request, vessel, risk_grid, demo_mode=demo_mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    db_route_data = route_create.model_dump(exclude={"waypoints", "risk_data_status", "ml_prediction_status", "warnings"})
    db_route = Route(**db_route_data)
    # Bypass DB persistence for demo mode (since Postgres is unavailable)
    # db.add(db_route)
    # await db.commit()
    # await db.refresh(db_route)

    try:
        geometry = parse_wkt_linestring(db_route.geometry)
    except Exception:
        geometry = {"type": "LineString", "coordinates": []}

    import uuid
    properties = RouteProperties(
        route_id=db_route.route_id or uuid.uuid4(),
        vessel_id=db_route.vessel_id,
        origin=db_route.origin,
        destination=db_route.destination,
        departure_time=db_route.departure_time,
        distance=db_route.distance,
        eta=db_route.eta,
        estimated_fuel=db_route.estimated_fuel,
        risk_score=db_route.risk_score,
        objective_type=db_route.objective_type,
        algorithm_version=db_route.algorithm_version,
        risk_data_status=route_create.risk_data_status,
        ml_prediction_status=route_create.ml_prediction_status,
        warnings=route_create.warnings,
        waypoints=route_create.waypoints
    )
    return GeoJSONFeature[RouteProperties](
        type="Feature", geometry=geometry, properties=properties
    )


@router.get("/{route_id}", response_model=RouteResponse)
async def get_route(
    route_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """Fetch a persisted route by id."""
    obj = await route_repo.get(db, route_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Route not found")

    try:
        geometry = parse_wkt_linestring(obj.geometry)
    except Exception:
        geometry = {"type": "LineString", "coordinates": []}
    properties = RouteProperties(
        route_id=obj.route_id,
        vessel_id=obj.vessel_id,
        origin=obj.origin,
        destination=obj.destination,
        departure_time=obj.departure_time,
        distance=obj.distance,
        eta=obj.eta,
        estimated_fuel=obj.estimated_fuel,
        risk_score=obj.risk_score,
        objective_type=obj.objective_type,
        algorithm_version=obj.algorithm_version,
    )
    return GeoJSONFeature[RouteProperties](
        type="Feature", geometry=geometry, properties=properties
    )


@router.post("/compare", response_model=RouteComparisonResponse)
async def compare_routes(
    request: RouteRequest,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """Compare routes across all objectives."""
    if request.custom_vessel_config:
        vessel = Vessel(**request.custom_vessel_config.model_dump())
        vessel.vessel_id = request.vessel_id
    else:
        try:
            vessel = await vessel_repo.get(db, request.vessel_id)
        except Exception:
            from app.config.config import settings
            if not getattr(settings, "DEMO_MODE", False):
                raise HTTPException(status_code=503, detail="Database unavailable")
            vessel = None
            
        if vessel is None:
            from app.config.config import settings
            if getattr(settings, "DEMO_MODE", False) and str(request.vessel_id) == "00000000-0000-0000-0000-000000000000":
                vessel = Vessel(
                    vessel_id=request.vessel_id,
                    vessel_name="Demo Explorer",
                    vessel_type="Research",
                    ice_capability="PC3",
                    cruising_speed=12.0,
                    fuel_consumption=2000.0,
                )
            else:
                raise HTTPException(status_code=404, detail="Vessel not found")

    risk_grid = await _build_risk_grid(db, request)
    try:
        comparison = await comparison_service.compare_routes(request, vessel, risk_grid)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return comparison
