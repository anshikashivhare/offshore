import uuid
from typing import Any, Dict
from typing import Optional as Opt

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
from app.utils.geojson import parse_wkt_linestring
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
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

    from sqlalchemy import func

    envelope = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
    st_intersects = getattr(RiskCell.geometry, "ST_Intersects", None)
    stmt = select(RiskCell)
    if st_intersects is not None:
        stmt = stmt.where(RiskCell.geometry.ST_Intersects(envelope))
    stmt = stmt.order_by(RiskCell.timestamp.desc()).limit(2000)
    rows = (await db.execute(stmt)).scalars().all()
    grid: Dict[Any, float] = {}
    for cell in rows:
        try:
            from app.utils.geojson import to_geojson_geometry

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
    vessel = await vessel_repo.get(db, request.vessel_id)
    if vessel is None:
        raise HTTPException(status_code=404, detail="Vessel not found")

    risk_grid = await _build_risk_grid(db, request)
    try:
        if request.objective_type.value == "shortest":
            route_create = await shortest_planner.plan_route(request, vessel, risk_grid)
        else:
            route_create = await astar_planner.plan_route(request, vessel, risk_grid)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    db_route = Route(**route_create.model_dump())
    db.add(db_route)
    await db.commit()
    await db.refresh(db_route)

    try:
        geometry = parse_wkt_linestring(db_route.geometry)
    except Exception:
        geometry = {"type": "LineString", "coordinates": []}

    properties = RouteProperties(
        route_id=db_route.route_id,
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
    vessel = await vessel_repo.get(db, request.vessel_id)
    if vessel is None:
        raise HTTPException(status_code=404, detail="Vessel not found")

    risk_grid = await _build_risk_grid(db, request)
    try:
        comparison = await comparison_service.compare_routes(request, vessel, risk_grid)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return comparison
