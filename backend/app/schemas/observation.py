import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.common import GeoJSONFeature

class SeaIceObservationProperties(BaseModel):
    id: uuid.UUID
    timestamp: datetime
    concentration: float
    thickness: Optional[float] = None
    ice_type: Optional[str] = None
    source: str
    data_quality: Optional[float] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2026-09-03T12:00:00Z",
                "concentration": 0.85,
                "thickness": 1.2,
                "ice_type": "First-year ice",
                "source": "Sentinel-1 SAR",
                "data_quality": 0.95
            }
        }
    )

class SeaIceObservationCreate(BaseModel):
    timestamp: datetime
    geometry: str # WKT or GeoJSON for creation
    concentration: float
    thickness: Optional[float] = None
    ice_type: Optional[str] = None
    source: str
    data_quality: Optional[float] = None
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2026-09-03T12:00:00Z",
                "geometry": "POINT(-60.1 -65.2)",
                "concentration": 0.85,
                "thickness": 1.2,
                "ice_type": "First-year ice",
                "source": "Sentinel-1 SAR",
                "data_quality": 0.95
            }
        }
    )
class WeatherObservationProperties(BaseModel):
    id: uuid.UUID
    timestamp: datetime
    wind_speed: float
    wind_direction: float
    temperature: float
    wave_height: float
    pressure: Optional[float] = None
    source: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2026-09-03T12:00:00Z",
                "wind_speed": 15.5,
                "wind_direction": 180.0,
                "temperature": -5.2,
                "wave_height": 2.5,
                "pressure": 1013.25,
                "source": "GFS"
            }
        }
    )

class WeatherObservationCreate(BaseModel):
    timestamp: datetime
    geometry: str
    wind_speed: float
    wind_direction: float
    temperature: float
    wave_height: float
    pressure: Optional[float] = None
    source: str
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2026-09-03T12:00:00Z",
                "geometry": "POINT(-60.1 -65.2)",
                "wind_speed": 15.5,
                "wind_direction": 180.0,
                "temperature": -5.2,
                "wave_height": 2.5,
                "pressure": 1013.25,
                "source": "GFS"
            }
        }
    )
class OceanObservationProperties(BaseModel):
    id: uuid.UUID
    timestamp: datetime
    current_speed: float
    current_direction: float
    sea_surface_temperature: float
    wave_information: Optional[str] = None
    source: str

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2026-09-03T12:00:00Z",
                "current_speed": 1.2,
                "current_direction": 90.0,
                "sea_surface_temperature": -1.5,
                "wave_information": "Swell 2m",
                "source": "Copernicus Marine Service"
            }
        }
    )

class OceanObservationCreate(BaseModel):
    timestamp: datetime
    geometry: str
    current_speed: float
    current_direction: float
    sea_surface_temperature: float
    wave_information: Optional[str] = None
    source: str
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2026-09-03T12:00:00Z",
                "geometry": "POINT(-60.1 -65.2)",
                "current_speed": 1.2,
                "current_direction": 90.0,
                "sea_surface_temperature": -1.5,
                "wave_information": "Swell 2m",
                "source": "Copernicus Marine Service"
            }
        }
    )
# API response types
SeaIceObservationResponse = GeoJSONFeature[SeaIceObservationProperties]
WeatherObservationResponse = GeoJSONFeature[WeatherObservationProperties]
OceanObservationResponse = GeoJSONFeature[OceanObservationProperties]

SeaIceObservationBase = SeaIceObservationCreate
WeatherObservationBase = WeatherObservationCreate
OceanObservationBase = OceanObservationCreate
