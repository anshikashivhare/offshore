import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.common import GeoJSONFeature

class IcebergBase(BaseModel):
    pass

class IcebergCreate(IcebergBase):
    pass

class IcebergProperties(IcebergBase):
    iceberg_id: uuid.UUID
    latest_detection_id: Optional[uuid.UUID] = None
    latest_detection_timestamp: Optional[datetime] = None
    n_detections: int = 0
    model_config = ConfigDict(from_attributes=True)

class IcebergDetectionProperties(BaseModel):
    id: uuid.UUID
    iceberg_id: uuid.UUID
    timestamp: datetime
    estimated_size: Optional[float] = None
    confidence: float
    source_imagery: Optional[str] = None
    detection_metadata: Optional[Dict[str, Any]] = None
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "iceberg_id": "123e4567-e89b-12d3-a456-426614174001",
                "timestamp": "2026-09-03T12:00:00Z",
                "estimated_size": 250.5,
                "confidence": 0.95,
                "source_imagery": "Sentinel-1 SAR",
                "detection_metadata": {"pixels": 150}
            }
        }
    )

class IcebergDetectionCreate(BaseModel):
    iceberg_id: uuid.UUID
    timestamp: datetime
    geometry: str
    estimated_size: Optional[float] = None
    confidence: float
    source_imagery: Optional[str] = None
    detection_metadata: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "iceberg_id": "123e4567-e89b-12d3-a456-426614174001",
                "timestamp": "2026-09-03T12:00:00Z",
                "geometry": "POINT(-60.1 -65.2)",
                "estimated_size": 250.5,
                "confidence": 0.95,
                "source_imagery": "Sentinel-1 SAR",
                "detection_metadata": {"pixels": 150}
            }
        }
    )

class IcebergTrajectoryPredictionProperties(BaseModel):
    id: uuid.UUID
    iceberg_id: uuid.UUID
    prediction_timestamp: datetime
    forecast_horizon: int
    uncertainty_representation: Optional[str] = None
    model_confidence: Optional[float] = None
    model_version: Optional[str] = None
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "iceberg_id": "123e4567-e89b-12d3-a456-426614174001",
                "prediction_timestamp": "2026-09-03T12:00:00Z",
                "forecast_horizon": 24,
                "uncertainty_representation": "POLYGON((...))",
                "model_confidence": 0.85,
                "model_version": "v1.2"
            }
        }
    )

class IcebergTrajectoryPredictionCreate(BaseModel):
    iceberg_id: uuid.UUID
    prediction_timestamp: datetime
    forecast_horizon: int
    predicted_geometry: str
    uncertainty_representation: Optional[str] = None
    model_confidence: Optional[float] = None
    model_version: Optional[str] = None
    
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "iceberg_id": "123e4567-e89b-12d3-a456-426614174001",
                "prediction_timestamp": "2026-09-03T12:00:00Z",
                "forecast_horizon": 24,
                "predicted_geometry": "LINESTRING(-60.1 -65.2, -60.0 -65.3)",
                "uncertainty_representation": "POLYGON((...))",
                "model_confidence": 0.85,
                "model_version": "v1.2"
            }
        }
    )

IcebergResponse = IcebergProperties
IcebergDetectionResponse = GeoJSONFeature[IcebergDetectionProperties]
IcebergTrajectoryPredictionResponse = GeoJSONFeature[IcebergTrajectoryPredictionProperties]

IcebergDetectionBase = IcebergDetectionCreate
IcebergTrajectoryPredictionBase = IcebergTrajectoryPredictionCreate
