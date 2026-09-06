import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import AlertSeverity
from app.schemas.common import GeoJSONFeature

class AlertProperties(BaseModel):
    id: uuid.UUID
    alert_type: str
    severity: AlertSeverity
    timestamp: datetime
    route_id: Optional[uuid.UUID] = None
    hazard_source: str
    message: str
    status: str
    triggering_metric: Optional[float] = None
    threshold: Optional[float] = None
    confidence: Optional[float] = None
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "alert_type": "iceberg",
                "severity": "critical",
                "timestamp": "2026-09-03T12:00:00Z",
                "route_id": "123e4567-e89b-12d3-a456-426614174001",
                "hazard_source": "iceberg_model",
                "message": "Predicted critical iceberg hazard region approaches within proximity buffer of the planned route.",
                "status": "active",
                "triggering_metric": 0.85,
                "threshold": 0.60,
                "confidence": 0.90
            }
        }
    )

class AlertCreate(BaseModel):
    alert_type: str
    severity: AlertSeverity
    location: str
    timestamp: datetime
    route_id: Optional[uuid.UUID] = None
    hazard_source: str
    message: str
    status: str = "active"
    triggering_metric: Optional[float] = None
    threshold: Optional[float] = None
    confidence: Optional[float] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "alert_type": "iceberg",
                "severity": "critical",
                "location": "POINT(-60.1 -65.2)",
                "timestamp": "2026-09-03T12:00:00Z",
                "route_id": "123e4567-e89b-12d3-a456-426614174001",
                "hazard_source": "iceberg_model",
                "message": "Predicted critical iceberg hazard region approaches within proximity buffer of the planned route.",
                "status": "active",
                "triggering_metric": 0.85,
                "threshold": 0.60,
                "confidence": 0.90
            }
        }
    )
class AlertBase(AlertCreate):
    pass

AlertResponse = GeoJSONFeature[AlertProperties]
