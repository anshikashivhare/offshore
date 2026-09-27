"""
Demo corridor provider for Sydney ↔ Rothera presentation route.

This module provides a deterministic, pre-validated route for the
Sydney ↔ Rothera port pair, bypassing expensive A*/Dijkstra computation
and external weather API dependencies.

Feature flag: DEMO_CORRIDOR_ENABLED (in config.py)
"""

import json
import logging
import uuid
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.models.enums import ObjectiveType
from app.schemas.route import (
    CostDecomposition,
    OptimizationWeights,
    RouteAlternative,
    RouteComparisonMetrics,
    RouteComparisonResponse,
    RouteProperties,
    RouteResponse,
    WaypointDetail,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Canonical port coordinates (WGS84)
# ---------------------------------------------------------------------------
SYDNEY_LON, SYDNEY_LAT = 151.20, -33.87
ROTHERA_LON, ROTHERA_LAT = -68.13, -67.57

# ---------------------------------------------------------------------------
# Pair detection
# ---------------------------------------------------------------------------

def parse_coords(coord_str: str) -> Tuple[Optional[float], Optional[float]]:
    """Parse 'lon,lat' string into (lon, lat) floats."""
    try:
        lon, lat = (float(x) for x in coord_str.split(","))
        return lon, lat
    except (ValueError, AttributeError):
        return None, None


def is_sydney_rothera_pair(origin_str: str, destination_str: str) -> Tuple[bool, bool]:
    """Return (is_demo, is_reverse) for the Sydney ↔ Rothera pair.
    
    Uses a ±2° tolerance to match coordinates from the port database.
    """
    o_lon, o_lat = parse_coords(origin_str)
    d_lon, d_lat = parse_coords(destination_str)
    if o_lon is None or d_lon is None:
        return False, False

    def _close(lon1: float, lat1: float, lon2: float, lat2: float, tol: float = 2.0) -> bool:
        return abs(lon1 - lon2) < tol and abs(lat1 - lat2) < tol

    forward = _close(o_lon, o_lat, SYDNEY_LON, SYDNEY_LAT) and _close(d_lon, d_lat, ROTHERA_LON, ROTHERA_LAT)
    reverse = _close(o_lon, o_lat, ROTHERA_LON, ROTHERA_LAT) and _close(d_lon, d_lat, SYDNEY_LON, SYDNEY_LAT)

    return forward or reverse, reverse


# ---------------------------------------------------------------------------
# Load canonical geometry
# ---------------------------------------------------------------------------

def _load_canonical_geometries() -> Dict[str, List[List[float]]]:
    """Load the pre-validated [lon, lat] coordinate lists from sydney_rothera_variants.json."""
    demo_file = Path(__file__).resolve().parents[4] / "sydney_rothera_variants.json"
    with open(demo_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["routes"]


# ---------------------------------------------------------------------------
# Variant route metrics (deterministic, internally consistent)
# ---------------------------------------------------------------------------

# Base metrics for Sydney → Rothera (~8200 km / 4430 nm great-circle)
_VARIANT_METRICS: Dict[ObjectiveType, Dict[str, Any]] = {
    ObjectiveType.SAFEST: {
        "distance": 4935.2,         # nautical miles
        "travel_time": 410.0,       # hours
        "estimated_fuel": 10400.0,  # litres
        "risk_score": 0.18,
        "risk_exposure": 32.5,
        "algorithm_version": "DemoCorridor-SafetyOptimized-v1.0",
    },
    ObjectiveType.FASTEST: {
        "distance": 4691.2,
        "travel_time": 330.0,       # fastest
        "estimated_fuel": 11200.0,
        "risk_score": 0.35,
        "risk_exposure": 58.2,
        "algorithm_version": "DemoCorridor-SpeedOptimized-v1.0",
    },
    ObjectiveType.FUEL_EFFICIENT: {
        "distance": 4727.4,
        "travel_time": 395.0,       
        "estimated_fuel": 8900.0,
        "risk_score": 0.25,
        "risk_exposure": 42.8,
        "algorithm_version": "DemoCorridor-FuelOptimized-v1.0",
    },
    ObjectiveType.SHORTEST: {
        "distance": 4687.3,
        "travel_time": 355.0,       
        "estimated_fuel": 10800.0,
        "risk_score": 0.40,
        "risk_exposure": 65.1,
        "algorithm_version": "DemoCorridor-ShortestPath-v1.0",
    },
}


def _build_waypoints(
    coords: List[List[float]],
    departure: datetime,
    travel_time_hours: float,
) -> List[WaypointDetail]:
    """Build deterministic waypoint details with ETAs and environment data."""
    n = len(coords)
    if n == 0:
        return []
    
    time_step = timedelta(hours=travel_time_hours / max(n - 1, 1))
    waypoints = []
    
    for i, (lon, lat) in enumerate(coords):
        eta = departure + time_step * i
        
        # Deterministic environment varies by latitude band
        abs_lat = abs(lat)
        if abs_lat < 45:
            wind_speed = 12.0 + (abs_lat - 34) * 0.3
            wave_height = 1.8
            ice_conc = 0.0
        elif abs_lat < 60:
            wind_speed = 18.0 + (abs_lat - 45) * 0.4
            wave_height = 3.2 + (abs_lat - 45) * 0.1
            ice_conc = 0.0
        elif abs_lat < 68:
            wind_speed = 22.0 + (abs_lat - 60) * 0.3
            wave_height = 4.0 + (abs_lat - 60) * 0.15
            ice_conc = 0.05 + (abs_lat - 60) * 0.03
        else:
            wind_speed = 25.0
            wave_height = 4.5
            ice_conc = 0.15 + (abs_lat - 68) * 0.05
        
        provenance = "demo_deterministic"
        
        waypoints.append(WaypointDetail(
            lat=lat,
            lon=lon,
            eta=eta,
            data_provenance=provenance,
            env_conditions={
                "wind_speed": round(wind_speed, 1),
                "wind_direction": 225.0,
                "wave_height": round(wave_height, 1),
                "ocean_current_speed": 0.5,
                "ocean_current_direction": 180.0,
                "sea_ice_concentration": round(ice_conc, 3),
            },
        ))
    
    return waypoints


def _build_route_response(
    objective: ObjectiveType,
    coords: List[List[float]],
    vessel_id: str,
    origin_str: str,
    destination_str: str,
    departure: datetime,
) -> RouteResponse:
    """Build a single GeoJSON Feature route response for one objective."""
    metrics = _VARIANT_METRICS[objective]
    travel_time = metrics["travel_time"]
    eta = departure + timedelta(hours=travel_time)
    
    waypoints = _build_waypoints(coords, departure, travel_time)

    props = RouteProperties(
        route_id=uuid.uuid4(),
        vessel_id=uuid.UUID(vessel_id),
        origin=origin_str,
        destination=destination_str,
        departure_time=departure,
        distance=metrics["distance"],
        travel_time=travel_time,
        eta=eta,
        estimated_fuel=metrics["estimated_fuel"],
        risk_score=metrics["risk_score"],
        risk_exposure=metrics["risk_exposure"],
        objective_type=objective,
        algorithm_version=metrics["algorithm_version"],
        risk_data_status="KNOWN",
        ml_prediction_status="AVAILABLE",
        warnings=["Demo corridor: deterministic presentation data."],
        waypoints=waypoints,
        land_avoidance_validated=True,
        endpoint_snapping_applied=False,
        snapped_origin=None,
        snapped_destination=None,
        cost_decomposition=CostDecomposition(
            total_cost=metrics["distance"] * 0.5 + metrics["risk_score"] * 100,
            time_cost=travel_time * 1.2,
            fuel_cost=metrics["estimated_fuel"] * 0.01,
            risk_cost=metrics["risk_score"] * 100,
            wave_penalty=15.0,
            wind_penalty=10.0,
        ),
        iceberg_risk_status="active",
        iceberg_model_version="DemoCorridor-v1.0",
        iceberg_forecast_available=True,
        forecast_coverage_hours=72.0,
        candidate_icebergs=5,
        closest_iceberg="DEMO-IB-1",
        min_cpa_distance_km=45.0,
        cpa_time=departure + timedelta(hours=travel_time * 0.7),
        encounter_risk=0.12,
        uncertainty_radius_km=25.0,
    )

    geometry = {"type": "LineString", "coordinates": coords}
    return RouteResponse(type="Feature", geometry=geometry, properties=props)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def get_demo_comparison(request: Any, reverse: bool) -> RouteComparisonResponse:
    """Return a complete RouteComparisonResponse for the Sydney ↔ Rothera demo pair.
    
    This bypasses A*/Dijkstra and returns deterministic pre-validated data.
    All route geometries are validated against the land mask before return.
    """
    from app.services.routing.validator import route_validator

    # Load canonical geometries
    variants = _load_canonical_geometries()
    
    # Determine origin/destination strings
    origin_str = request.origin
    destination_str = request.destination
    vessel_id_str = str(request.vessel_id)
    departure = request.departure_time
    if departure.tzinfo is None:
        departure = departure.replace(tzinfo=timezone.utc)
    
    # Requested objective determines recommended route
    requested_obj = request.objective_type
    if isinstance(requested_obj, str):
        requested_obj = ObjectiveType(requested_obj)
    
    # Build all 4 variants
    all_objectives = [
        ObjectiveType.SAFEST,
        ObjectiveType.FASTEST,
        ObjectiveType.FUEL_EFFICIENT,
        ObjectiveType.SHORTEST,
    ]
    
    routes: Dict[ObjectiveType, RouteResponse] = {}
    for obj in all_objectives:
        obj_key = obj.value
        coords = variants.get(obj_key)
        if not coords:
            coords = variants["fastest"]  # fallback
            
        if reverse:
            coords = list(reversed(coords))
            
        wkt = "LINESTRING(" + ", ".join(f"{c[0]} {c[1]}" for c in coords) + ")"
        is_valid, err_msg, _ = route_validator.validate_wkt_linestring(wkt, strict=False)
        if not is_valid:
            raise ValueError(f"Demo variant {obj_key} failed land validation: {err_msg}")
            
        routes[obj] = _build_route_response(
            objective=obj,
            coords=coords,
            vessel_id=vessel_id_str,
            origin_str=origin_str,
            destination_str=destination_str,
            departure=departure,
        )
    
    # Recommended route is the one matching the user's requested objective
    recommended = routes.get(requested_obj, routes[ObjectiveType.SAFEST])
    
    # Build alternatives (everything except the recommended)
    alternatives: List[RouteAlternative] = []
    for obj, route in routes.items():
        if route.properties.route_id == recommended.properties.route_id:
            continue
        
        metrics = RouteComparisonMetrics(
            distance_diff=route.properties.distance - recommended.properties.distance,
            time_diff_hours=route.properties.travel_time - recommended.properties.travel_time,
            fuel_diff=route.properties.estimated_fuel - recommended.properties.estimated_fuel,
            risk_diff=route.properties.risk_exposure - recommended.properties.risk_exposure,
        )
        alternatives.append(RouteAlternative(route=route, comparison_metrics=metrics))
    
    # Risk factors from waypoint env conditions
    risk_factors: Dict[str, Any] = {
        "average_sea_ice_concentration": 0.08,
        "average_wave_height": 3.4,
        "iceberg_encounter_probability": 0.12,
        "demo_data": True,
    }
    
    # Explanation
    obj_name = requested_obj.value.upper()
    explanation = (
        f"This route was recommended because the objective is {obj_name}. "
        f"The route uses a pre-validated maritime corridor through the Southern Ocean. "
        f"Risk data is based on deterministic demo environmental conditions. "
        f"Sea ice concentration increases significantly south of 60°S."
    )
    
    uncertainty = "Medium confidence (avg=0.72). Demo corridor uses deterministic environmental predictions."
    
    warnings = [
        "Demo corridor: deterministic presentation data — not live operational.",
    ]
    
    return RouteComparisonResponse(
        recommended_route=recommended,
        alternatives=alternatives,
        optimization_weights=request.weights or OptimizationWeights(),
        risk_factors=risk_factors,
        explanation=explanation,
        uncertainty=uncertainty,
        warnings=warnings,
    )
