import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ForecastRequest(BaseModel):
    horizon_days: int = Field(..., description="Forecast horizon in days")
    region: Dict[str, float] = Field(
        ..., description="Bounding box dictionary: min_lon, min_lat, max_lon, max_lat"
    )
    initialization_time: Optional[datetime] = Field(
        None, description="Time to initialize the forecast. Defaults to now."
    )
    model_version: Optional[str] = Field(
        "1.0", description="Model version or identifier to use"
    )

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "horizon_days": 7,
                "region": {
                    "min_lon": -65.0,
                    "min_lat": -70.0,
                    "max_lon": -55.0,
                    "max_lat": -60.0,
                },
                "initialization_time": "2026-09-03T00:00:00Z",
                "model_version": "2.1",
            }
        },
    )

    @field_validator("horizon_days")
    @classmethod
    def validate_horizon(cls, v: int) -> int:
        if v < 1 or v > 30:
            raise ValueError("Forecast horizon must be between 1 and 30 days.")
        return v

    @field_validator("region")
    @classmethod
    def validate_region(cls, v: Dict[str, float]) -> Dict[str, float]:
        required_keys = {"min_lon", "min_lat", "max_lon", "max_lat"}
        if not required_keys.issubset(v.keys()):
            raise ValueError(f"Region must contain keys: {required_keys}")

        if v["min_lon"] < -180 or v["max_lon"] > 180:
            raise ValueError("Longitudes must be between -180 and 180")

        if v["min_lat"] < -90 or v["max_lat"] > 90:
            raise ValueError("Latitudes must be between -90 and 90")

        if v["min_lon"] >= v["max_lon"]:
            raise ValueError("min_lon must be less than max_lon")

        if v["min_lat"] >= v["max_lat"]:
            raise ValueError("min_lat must be less than max_lat")

        return v


class ForecastResult(BaseModel):
    forecast_id: str
    grid_metadata: Dict[str, Any]
    timestamp: datetime
    horizon_days: int
    region: Dict[str, float]
    predicted_concentration: (
        Any  # Could be nested lists or a reference to a raster file
    )
    confidence: Optional[float] = None
    model_metadata: Dict[str, Any]
    quality_flags: List[str] = Field(default_factory=list)

    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "forecast_id": "fc_8e94b2a",
                "grid_metadata": {"resolution_deg": 0.1, "rows": 100, "cols": 100},
                "timestamp": "2026-09-03T12:00:00Z",
                "horizon_days": 7,
                "region": {
                    "min_lon": -65.0,
                    "min_lat": -70.0,
                    "max_lon": -55.0,
                    "max_lat": -60.0,
                },
                "predicted_concentration": [[0.8, 0.9], [0.1, 0.0]],
                "confidence": 0.88,
                "model_metadata": {"name": "AntarcticIceCast", "version": "2.1"},
                "quality_flags": ["HIGH_CONFIDENCE"],
            }
        },
    )
