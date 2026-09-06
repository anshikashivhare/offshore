import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import ObjectiveType
from app.schemas.common import GeoJSONFeature

class RouteProperties(BaseModel):
    route_id: uuid.UUID
    vessel_id: uuid.UUID
    origin: str
    destination: str
    departure_time: datetime
    distance: float
    eta: datetime
    estimated_fuel: float
    risk_score: float
    objective_type: ObjectiveType
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
                "eta": "2026-09-04T18:30:00Z",
                "estimated_fuel": 12.5,
                "risk_score": 0.15,
                "objective_type": "safest",
                "algorithm_version": "v2.0"
            }
        }
    )

class OptimizationWeights(BaseModel):
    alpha: float = 0.33  # Fuel
    beta: float = 0.33   # Time
    gamma: float = 0.34  # Risk

class RouteRequest(BaseModel):
    origin: str  # e.g. "lon,lat"
    destination: str
    vessel_id: uuid.UUID
    departure_time: datetime
    objective_type: ObjectiveType = ObjectiveType.SAFEST
    weights: Optional[OptimizationWeights] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "origin": "-60.1,-65.2",
                "destination": "-55.5,-60.1",
                "vessel_id": "123e4567-e89b-12d3-a456-426614174001",
                "departure_time": "2026-09-03T12:00:00Z",
                "objective_type": "safest",
                "weights": {
                    "alpha": 0.33,
                    "beta": 0.33,
                    "gamma": 0.34
                }
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
    eta: datetime
    estimated_fuel: float
    risk_score: float
    objective_type: ObjectiveType
    algorithm_version: Optional[str] = None

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
    contributing_risk_factors: dict
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
                        "coordinates": [[-60.1, -65.2], [-55.5, -60.1]]
                    },
                    "properties": {
                        "route_id": "123e4567-e89b-12d3-a456-426614174000",
                        "vessel_id": "123e4567-e89b-12d3-a456-426614174001",
                        "origin": "-60.1,-65.2",
                        "destination": "-55.5,-60.1",
                        "departure_time": "2026-09-03T12:00:00Z",
                        "distance": 350.5,
                        "eta": "2026-09-04T18:30:00Z",
                        "estimated_fuel": 12.5,
                        "risk_score": 0.15,
                        "objective_type": "safest",
                        "algorithm_version": "v2.0"
                    }
                },
                "alternatives": [],
                "optimization_weights": {
                    "alpha": 0.33,
                    "beta": 0.33,
                    "gamma": 0.34
                },
                "contributing_risk_factors": {
                    "iceberg_risk": 0.8,
                    "weather_risk": 0.2
                },
                "explanation": "Route B was recommended because predicted iceberg exposure is lower...",
                "uncertainty": "Moderate uncertainty in iceberg prediction",
                "warnings": ["High wind speed predicted near destination"]
            }
        }
    )
