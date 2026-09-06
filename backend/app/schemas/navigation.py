import uuid
from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ObjectiveType
from app.schemas.route import RouteComparisonResponse, OptimizationWeights
from app.schemas.alert import AlertResponse

class NavigationScenarioRequest(BaseModel):
    origin: str = Field(..., description="Longitude,Latitude of origin")
    destination: str = Field(..., description="Longitude,Latitude of destination")
    vessel_id: uuid.UUID
    departure_time: datetime
    forecast_horizon: int = Field(24, description="Forecast horizon in hours")
    navigation_priority: ObjectiveType = ObjectiveType.SAFEST
    custom_weights: Optional[OptimizationWeights] = None
    optional_environmental_config: Optional[Dict[str, float]] = Field(
        None, description="Risk weight overrides"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "origin": "-60.1,-65.2",
                "destination": "-55.5,-60.1",
                "vessel_id": "123e4567-e89b-12d3-a456-426614174001",
                "departure_time": "2026-09-03T12:00:00Z",
                "forecast_horizon": 24,
                "navigation_priority": "safest",
                "custom_weights": {
                    "alpha": 0.33,
                    "beta": 0.33,
                    "gamma": 0.34
                }
            }
        }
    )

class NavigationScenarioResponse(BaseModel):
    scenario_metadata: dict
    recommended_route: dict
    alternatives: List[dict]
    environmental_summary: dict
    alerts: List[AlertResponse]
    explanation: str
    uncertainty: str
    processing_metadata: dict

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scenario_metadata": {
                    "vessel_name": "RRS Sir David Attenborough",
                    "origin": "-60.1,-65.2",
                    "destination": "-55.5,-60.1",
                    "departure_time": "2026-09-03T12:00:00Z"
                },
                "recommended_route": {
                    "type": "Feature",
                    "properties": {
                        "distance": 350.5,
                        "eta": "2026-09-04T18:30:00Z",
                        "estimated_fuel": 12.5,
                        "risk_score": 0.15
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[-60.1, -65.2], [-55.5, -60.1]]
                    }
                },
                "alternatives": [],
                "environmental_summary": {
                    "iceberg_risk": 0.8,
                    "weather_risk": 0.2
                },
                "alerts": [],
                "explanation": "Route was recommended due to zero iceberg exposure.",
                "uncertainty": "Low",
                "processing_metadata": {
                    "processing_time_sec": 1.2
                }
            }
        }
    )
