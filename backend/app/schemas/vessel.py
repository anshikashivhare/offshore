import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class VesselBase(BaseModel):
    vessel_name: str = Field(..., description="Name of the vessel")
    imo_number: Optional[str] = Field(None, description="IMO number")
    mmsi: Optional[str] = Field(None, description="MMSI number")
    flag_country: Optional[str] = Field(None, description="Flag country")
    vessel_type: str = Field(
        ..., description="Type of the vessel (e.g., Icebreaker, Cargo)"
    )
    max_speed: Optional[float] = Field(None, description="Maximum speed in knots")
    cruising_speed: float = Field(..., description="Cruising speed in knots")
    ice_capability: Optional[str] = Field(
        None, description="Ice class rating (e.g., Polar Class 1)"
    )
    icebreaking_capability: Optional[str] = Field(None, description="Icebreaking capability details")
    polar_operating_capability: Optional[str] = Field(None, description="Polar operating capability details")
    length_m: Optional[float] = Field(None, description="Length in meters")
    beam_m: Optional[float] = Field(None, description="Beam in meters")
    draft_m: Optional[float] = Field(None, description="Draft in meters")
    fuel_type: Optional[str] = Field(None, description="Fuel type")
    fuel_consumption: float = Field(..., description="Fuel consumption in tons per day")
    passenger_capacity: Optional[int] = Field(None, description="Passenger capacity")
    cargo_capacity: Optional[str] = Field(None, description="Cargo capacity")
    data_source: Optional[str] = Field(None, description="Source of the data")
    last_updated_timestamp: Optional[str] = Field(None, description="Last updated timestamp")
    verification_status: Optional[str] = Field(None, description="Verification status")
    operational_limits: Optional[Dict[str, Any]] = Field(
        None, description="Custom operational limits for routing"
    )

class VesselCreate(VesselBase):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "vessel_name": "RRS Sir David Attenborough",
                "imo_number": "9798222",
                "mmsi": "232024107",
                "flag_country": "United Kingdom",
                "vessel_type": "Research Icebreaker",
                "max_speed": 15.0,
                "cruising_speed": 13.0,
                "ice_capability": "Polar Class 4",
                "polar_operating_capability": "60 days endurance",
                "length_m": 129.0,
                "beam_m": 24.0,
                "draft_m": 7.0,
                "fuel_type": "Marine Diesel Oil",
                "fuel_consumption": 25.5,
                "data_source": "https://www.bas.ac.uk",
                "verification_status": "Verified",
                "operational_limits": {
                    "max_ice_thickness_m": 1.5,
                    "max_wave_height_m": 6.0,
                },
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
                "imo_number": "9798222",
                "mmsi": "232024107",
                "flag_country": "United Kingdom",
                "vessel_type": "Research Icebreaker",
                "max_speed": 15.0,
                "cruising_speed": 13.0,
                "ice_capability": "Polar Class 4",
                "polar_operating_capability": "60 days endurance",
                "length_m": 129.0,
                "beam_m": 24.0,
                "draft_m": 7.0,
                "fuel_type": "Marine Diesel Oil",
                "fuel_consumption": 25.5,
                "data_source": "https://www.bas.ac.uk",
                "verification_status": "Verified",
                "operational_limits": {
                    "max_ice_thickness_m": 1.5,
                    "max_wave_height_m": 6.0,
                },
            }
        },
    )
