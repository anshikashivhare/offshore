import uuid
from datetime import datetime
from typing import Optional

from app.models.enums import ObjectiveType
from app.schemas.common import GeoJSONFeature
from pydantic import BaseModel, ConfigDict, field_validator
from app.utils.coordinates import parse_wgs84_lon_lat


from typing import Optional, List, Dict, Any

class WaypointDetail(BaseModel):
    lat: float
    lon: float
    eta: datetime
    data_provenance: str
    env_conditions: Dict[str, Any]
class RiskGridData(BaseModel):
    cells: Dict[Any, float] = {}
    status: str = "unavailable"
    ml_status: str = "unavailable"
    warnings: List[str] = []

class CostDecomposition(BaseModel):
    total_cost: float = 0.0
    time_cost: float = 0.0
    fuel_cost: float = 0.0
    risk_cost: float = 0.0
    wave_penalty: float = 0.0
    wind_penalty: float = 0.0

class RouteProperties(BaseModel):
    route_id: uuid.UUID
    vessel_id: uuid.UUID
    origin: str
    destination: str
    departure_time: datetime
    distance: float
    travel_time: float
    eta: datetime
    estimated_fuel: float
    risk_score: float
    risk_exposure: float
    objective_type: ObjectiveType
    algorithm_version: Optional[str] = None
    risk_data_status: Optional[str] = "unknown"
    ml_prediction_status: Optional[str] = "unavailable"
    warnings: Optional[List[str]] = []
    waypoints: Optional[List[WaypointDetail]] = None
    # Land avoidance validation metadata
    land_avoidance_validated: Optional[bool] = None
    endpoint_snapping_applied: Optional[bool] = None
    snapped_origin: Optional[str] = None  # "lon,lat" if snapped
    snapped_destination: Optional[str] = None  # "lon,lat" if snapped
    cost_decomposition: Optional[CostDecomposition] = None
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "route_id": "123e4567-e89b-12d3-a456-426614174000",
                "vessel_id": "123e4567-e89b-12d3-a456-426614174001",
                "origin": "-60.1,-65.2",
                "destination": "-55.5,-60.1",
                "departure_time": "2026-09-03T12:00:00Z",
                "distance": 350.5,
                "travel_time": 30.5,
                "eta": "2026-09-04T18:30:00Z",
                "estimated_fuel": 12.5,
                "risk_score": 0.15,
                "risk_exposure": 52.57,
                "objective_type": "safest",
                "algorithm_version": "AStar-4D-TimeAware-v1.0",
                "waypoints": []
            }
        },
    )


class OptimizationWeights(BaseModel):
    alpha: float = 0.33  # Fuel
    beta: float = 0.33  # Time
    gamma: float = 0.34  # Risk


from app.schemas.vessel import VesselCreate

class RouteRequest(BaseModel):
    origin: str  # e.g. "lon,lat" in EPSG:4326 / WGS84
    destination: str
    vessel_id: uuid.UUID
    departure_time: datetime
    objective_type: ObjectiveType = ObjectiveType.SAFEST
    weights: Optional[OptimizationWeights] = None
    custom_vessel_config: Optional[VesselCreate] = None

    @field_validator("origin", "destination")
    @classmethod
    def require_wgs84_lon_lat(cls, value: str) -> str:
        """Reject invalid, swapped, or projected coordinate inputs early."""
        parse_wgs84_lon_lat(value)
        return value

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "origin": "-60.1,-65.2",
                "destination": "-55.5,-60.1",
                "vessel_id": "123e4567-e89b-12d3-a456-426614174001",
                "departure_time": "2026-09-03T12:00:00Z",
                "objective_type": "safest",
                "weights": {"alpha": 0.33, "beta": 0.33, "gamma": 0.34},
            }
        }
    )


class RouteCreate(BaseModel):
    origin: str
    destination: str
    vessel_id: uuid.UUID
    departure_time: datetime
    geometry: str
    distance: float
    travel_time: float
    eta: datetime
    estimated_fuel: float
    risk_score: float
    risk_exposure: float
    objective_type: ObjectiveType
    algorithm_version: Optional[str] = None
    risk_data_status: Optional[str] = "unknown"
    ml_prediction_status: Optional[str] = "unavailable"
    warnings: Optional[List[str]] = []
    waypoints: Optional[List[WaypointDetail]] = None
    # Land avoidance validation metadata
    land_avoidance_validated: Optional[bool] = None
    endpoint_snapping_applied: Optional[bool] = None
    snapped_origin: Optional[str] = None
    snapped_destination: Optional[str] = None
    cost_decomposition: Optional[CostDecomposition] = None

class RouteBase(RouteCreate):
    pass


RouteResponse = GeoJSONFeature[RouteProperties]

from typing import List


class RouteComparisonMetrics(BaseModel):
    distance_diff: float
    time_diff_hours: float
    fuel_diff: float
    risk_diff: float


class RouteAlternative(BaseModel):
    route: RouteResponse
    comparison_metrics: RouteComparisonMetrics


class RouteComparisonResponse(BaseModel):
    recommended_route: RouteResponse
    alternatives: List[RouteAlternative]
    optimization_weights: OptimizationWeights
    risk_factors: dict
    explanation: str
    uncertainty: str
    warnings: List[str]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "recommended_route": {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[-60.1, -65.2], [-55.5, -60.1]],
                    },
                    "properties": {
                        "route_id": "123e4567-e89b-12d3-a456-426614174000",
                        "vessel_id": "123e4567-e89b-12d3-a456-426614174001",
                        "origin": "-60.1,-65.2",
                        "destination": "-55.5,-60.1",
                        "departure_time": "2026-09-03T12:00:00Z",
                        "distance": 350.5,
                        "travel_time": 30.5,
                        "eta": "2026-09-04T18:30:00Z",
                        "estimated_fuel": 12.5,
                        "risk_score": 0.15,
                        "risk_exposure": 52.57,
                        "objective_type": "safest",
                        "algorithm_version": "v2.0",
                    },
                },
                "alternatives": [],
                "optimization_weights": {"alpha": 0.33, "beta": 0.33, "gamma": 0.34},
                "risk_factors": {"iceberg_risk": 0.8, "weather_risk": 0.2},
                "explanation": "Route B was recommended because predicted iceberg exposure is lower...",
                "uncertainty": "Moderate uncertainty in iceberg prediction",
                "warnings": ["High wind speed predicted near destination"],
            }
        }
    )
