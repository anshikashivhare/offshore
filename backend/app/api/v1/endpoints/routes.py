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
from app.schemas.route import (RouteComparisonResponse, RouteProperties, RiskGridData,
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


async def _build_risk_grid(db: AsyncSession, request: RouteRequest) -> RiskGridData:
    """Fetch the most recent RiskCell rows that intersect the route bbox and
    expose them as a dict keyed by rounded (lat, lon) centroid coordinates.

    The A* and Dijkstra planners both consume a dict-of-float risk grid.
    """
    from app.config.config import settings

    if getattr(settings, "DEMO_MODE", False):
        try:
            # Check if DB is up before assuming we can't do anything
            await db.execute(select(1))
        except Exception:
            return RiskGridData(cells={}, status="UNAVAILABLE", ml_status="AVAILABLE", warnings=["Risk data could not be loaded because the configured PostgreSQL database is unavailable."])

    try:
        origin_lon, origin_lat = (float(x) for x in request.origin.split(","))
        dest_lon, dest_lat = (float(x) for x in request.destination.split(","))
    except (ValueError, AttributeError):
        return RiskGridData(cells={}, status="UNAVAILABLE", ml_status="UNAVAILABLE", warnings=["Invalid origin/destination for risk bounding box."])
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
        msg = "Risk data could not be loaded because the configured PostgreSQL database is unavailable."
        return RiskGridData(cells={}, status="UNAVAILABLE", ml_status="AVAILABLE", warnings=[msg])
        
    grid: Dict[Any, float] = {}
    ml_used = False
    for cell in rows:
        if cell.data_source == "ml_forecast":
            ml_used = True
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
            
    ml_status = "AVAILABLE" if ml_used else "UNAVAILABLE"
    status = "KNOWN"
    warnings = [] if grid else ["No risk cells found for this region."]
    return RiskGridData(cells=grid, status=status, ml_status=ml_status, warnings=warnings)


@router.post("/plan", response_model=RouteResponse, status_code=status.HTTP_201_CREATED)
async def plan_route(
    request: RouteRequest,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """Plan a route using A* over the latest persisted risk surface."""
    from app.config.config import settings
    from app.services.routing.validator import route_validator, RouteValidationError

    # Use custom configuration if provided
    if request.custom_vessel_config:
        vessel = Vessel(**request.custom_vessel_config.model_dump())
        vessel.vessel_id = request.vessel_id # Preserve the ID
    elif getattr(settings, "DEMO_MODE", False):
        import json
        from pathlib import Path
        try:
            vessels_path = Path(__file__).resolve().parents[4] / "data" / "vessels.json"
            with vessels_path.open("r", encoding="utf-8") as f:
                all_vessels = json.load(f)
            v_id_str = str(request.vessel_id)
            vessel_data = next((v for v in all_vessels if str(v.get("vessel_id")) == v_id_str), None)
            if not vessel_data and all_vessels:
                vessel_data = all_vessels[0]
            vessel = Vessel(**vessel_data) if vessel_data else None
        except Exception:
            vessel = None
    else:
        try:
            vessel = await vessel_repo.get(db, request.vessel_id)
        except Exception as exc:
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

    snapped_origin = astar_planner.grid_builder.snap_to_water(origin_node, max_radius_degrees=3.0)
    if snapped_origin is None:
        raise HTTPException(status_code=400, detail="Origin port is on land and no navigable water found within 3.0° search radius.")

    snapped_dest = astar_planner.grid_builder.snap_to_water(dest_node, max_radius_degrees=3.0)
    if snapped_dest is None:
        raise HTTPException(status_code=400, detail="Destination port is on land and no navigable water found within 3.0° search radius.")

    # Track whether snapping was applied
    origin_snapped = (snapped_origin.lat != origin_lat or snapped_origin.lon != origin_lon)
    dest_snapped = (snapped_dest.lat != dest_lat or snapped_dest.lon != dest_lon)
    endpoint_snapping_applied = origin_snapped or dest_snapped

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

    # CRITICAL: Validate route for land avoidance before returning to user
    try:
        is_valid, error_msg, details = route_validator.validate_wkt_linestring(
            route_create.geometry, strict=False
        )
        if not is_valid:
            # Route generation failed to avoid land - this is a critical bug
            raise HTTPException(
                status_code=500,
                detail=f"Route validation failed: {error_msg}. This should not happen - please report this bug."
            )
        land_avoidance_validated = True
    except RouteValidationError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Route crosses land: {str(exc)}. This should not happen - please report this bug."
        )
    except Exception as exc:
        # Validation itself failed - still return route but mark as unvalidated
        land_avoidance_validated = False
        if route_create.warnings is None:
            route_create.warnings = []
        route_create.warnings.append(f"Land avoidance validation failed: {str(exc)}")

    # Add validation metadata to route
    route_create.land_avoidance_validated = land_avoidance_validated
    route_create.endpoint_snapping_applied = endpoint_snapping_applied
    if endpoint_snapping_applied:
        route_create.snapped_origin = f"{snapped_origin.lon},{snapped_origin.lat}"
        route_create.snapped_destination = f"{snapped_dest.lon},{snapped_dest.lat}"

    exclude_fields = {
        "waypoints", "risk_data_status", "ml_prediction_status", "warnings", 
        "land_avoidance_validated", "endpoint_snapping_applied", "snapped_origin", 
        "snapped_destination", "cost_decomposition",
        "iceberg_risk_status", "iceberg_model_version", "iceberg_forecast_available",
        "forecast_coverage_hours", "candidate_icebergs", "closest_iceberg",
        "min_cpa_distance_km", "cpa_time", "encounter_risk", "uncertainty_radius_km"
    }
    db_route_data = route_create.model_dump(exclude=exclude_fields)
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
        travel_time=db_route.travel_time,
        eta=db_route.eta,
        estimated_fuel=db_route.estimated_fuel,
        risk_score=db_route.risk_score,
        risk_exposure=db_route.risk_exposure,
        objective_type=db_route.objective_type,
        algorithm_version=db_route.algorithm_version,
        risk_data_status=route_create.risk_data_status,
        ml_prediction_status=route_create.ml_prediction_status,
        warnings=route_create.warnings,
        waypoints=route_create.waypoints,
        land_avoidance_validated=route_create.land_avoidance_validated,
        endpoint_snapping_applied=route_create.endpoint_snapping_applied,
        snapped_origin=route_create.snapped_origin,
        snapped_destination=route_create.snapped_destination,
        cost_decomposition=route_create.cost_decomposition,
        iceberg_risk_status=route_create.iceberg_risk_status,
        iceberg_model_version=route_create.iceberg_model_version,
        iceberg_forecast_available=route_create.iceberg_forecast_available,
        forecast_coverage_hours=route_create.forecast_coverage_hours,
        candidate_icebergs=route_create.candidate_icebergs,
        closest_iceberg=route_create.closest_iceberg,
        min_cpa_distance_km=route_create.min_cpa_distance_km,
        cpa_time=route_create.cpa_time,
        encounter_risk=route_create.encounter_risk,
        uncertainty_radius_km=route_create.uncertainty_radius_km
    )
    return GeoJSONFeature[RouteProperties](
        type="Feature", geometry=geometry, properties=properties
    )


@router.get("/", response_model=list[RouteResponse])
async def list_routes(
    db: AsyncSession = Depends(deps.get_db),
    pagination: deps.PaginationParams = Depends(),
) -> Any:
    """Fetch recent routes."""
    from app.config.config import settings
    if getattr(settings, "DEMO_MODE", False):
        return []
    try:
        routes = await route_repo.get_multi(db, skip=pagination.skip, limit=pagination.limit)
        results = []
        for r in routes:
            try:
                geom = parse_wkt_linestring(r.geometry)
            except Exception:
                geom = {"type": "LineString", "coordinates": []}
            props = RouteProperties(
                route_id=r.route_id,
                vessel_id=r.vessel_id,
                origin=r.origin,
                destination=r.destination,
                departure_time=r.departure_time,
                distance=r.distance,
                travel_time=r.travel_time,
                eta=r.eta,
                estimated_fuel=r.estimated_fuel,
                risk_score=r.risk_score,
                risk_exposure=r.risk_exposure,
                objective_type=r.objective_type,
                algorithm_version=r.algorithm_version,
            )
            results.append(GeoJSONFeature[RouteProperties](type="Feature", geometry=geom, properties=props))
        return results
    except Exception:
        return []


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
        travel_time=obj.travel_time,
        eta=obj.eta,
        estimated_fuel=obj.estimated_fuel,
        risk_score=obj.risk_score,
        risk_exposure=obj.risk_exposure,
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
    from app.config.config import settings
    demo_mode = getattr(settings, "DEMO_MODE", False)

    if request.custom_vessel_config:
        vessel = Vessel(**request.custom_vessel_config.model_dump())
        vessel.vessel_id = request.vessel_id
    elif demo_mode:
        import json
        from pathlib import Path
        try:
            vessels_path = Path(__file__).resolve().parents[4] / "data" / "vessels.json"
            with vessels_path.open("r", encoding="utf-8") as f:
                all_vessels = json.load(f)
            v_id_str = str(request.vessel_id)
            vessel_data = next((v for v in all_vessels if str(v.get("vessel_id")) == v_id_str), None)
            if not vessel_data and all_vessels:
                vessel_data = all_vessels[0]
            vessel = Vessel(**vessel_data) if vessel_data else None
        except Exception:
            vessel = None
    else:
        try:
            vessel = await vessel_repo.get(db, request.vessel_id)
        except Exception as exc:
            raise HTTPException(status_code=503, detail="Database unavailable") from exc

    if vessel is None:
        raise HTTPException(status_code=404, detail="Vessel not found")

    risk_grid = await _build_risk_grid(db, request)
    try:
        comparison = await comparison_service.compare_routes(request, vessel, risk_grid, demo_mode=demo_mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return comparison
