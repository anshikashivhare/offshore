import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.schemas.common import GeoJSONFeature
from app.models.enums import RiskCategory

class RiskCellProperties(BaseModel):
    id: uuid.UUID
    timestamp: datetime
    ice_risk: float
    iceberg_risk: float
    weather_risk: float
    current_risk: float
    composite_risk: float
    risk_category: RiskCategory
    confidence_score: float = 1.0
    missing_data_flags: dict = {}
    metadata_info: dict = {}
    model_config = ConfigDict(
        from_attributes=True,
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2026-09-03T12:00:00Z",
                "ice_risk": 0.2,
                "iceberg_risk": 0.8,
                "weather_risk": 0.1,
                "current_risk": 0.05,
                "composite_risk": 0.65,
                "risk_category": "moderate",
                "confidence_score": 0.9,
                "missing_data_flags": {"currents": True},
                "metadata_info": {"model_version": "v1.1"}
            }
        }
    )

class RiskCellCreate(BaseModel):
    geometry: str
    timestamp: datetime
    ice_risk: float
    iceberg_risk: float
    weather_risk: float
    current_risk: float
    composite_risk: float
    risk_category: RiskCategory
    confidence_score: float = 1.0
    missing_data_flags: dict = {}
    metadata_info: dict = {}
    
    model_config = ConfigDict(
        protected_namespaces=(),
        json_schema_extra={
            "example": {
                "geometry": "POLYGON((-60 -65, -60 -64, -59 -64, -59 -65, -60 -65))",
                "timestamp": "2026-09-03T12:00:00Z",
                "ice_risk": 0.2,
                "iceberg_risk": 0.8,
                "weather_risk": 0.1,
                "current_risk": 0.05,
                "composite_risk": 0.65,
                "risk_category": "moderate",
                "confidence_score": 0.9,
                "missing_data_flags": {"currents": True},
                "metadata_info": {"model_version": "v1.1"}
            }
        }
    )

class RiskCellBase(RiskCellCreate):
    pass

RiskCellResponse = GeoJSONFeature[RiskCellProperties]
