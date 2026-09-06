from pydantic import BaseModel, Field, ConfigDict
import uuid
from typing import Optional, Dict, Any

class VesselBase(BaseModel):
    vessel_name: str = Field(..., description="Name of the vessel")
    vessel_type: str = Field(..., description="Type of the vessel (e.g., Icebreaker, Cargo)")
    cruising_speed: float = Field(..., description="Cruising speed in knots")
    fuel_consumption: float = Field(..., description="Fuel consumption in tons per day")
    ice_capability: str = Field(..., description="Ice class rating (e.g., Polar Class 1)")
    operational_limits: Optional[Dict[str, Any]] = Field(None, description="Custom operational limits for routing")

class VesselCreate(VesselBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "vessel_name": "RRS Sir David Attenborough",
                "vessel_type": "Research Icebreaker",
                "cruising_speed": 13.0,
                "fuel_consumption": 25.5,
                "ice_capability": "Polar Class 4",
                "operational_limits": {
                    "max_ice_thickness_m": 1.5,
                    "max_wave_height_m": 6.0
                }
            }
        }
    )

class VesselResponse(VesselBase):
    vessel_id: uuid.UUID = Field(..., description="Unique identifier for the vessel")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "vessel_id": "123e4567-e89b-12d3-a456-426614174000",
                "vessel_name": "RRS Sir David Attenborough",
                "vessel_type": "Research Icebreaker",
                "cruising_speed": 13.0,
                "fuel_consumption": 25.5,
                "ice_capability": "Polar Class 4",
                "operational_limits": {
                    "max_ice_thickness_m": 1.5,
                    "max_wave_height_m": 6.0
                }
            }
        }
    )
