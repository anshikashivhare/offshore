from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field

class WaypointRequest(BaseModel):
    lat: float
    lon: float
    eta: Optional[datetime] = None

class LiveEnvironmentRequest(BaseModel):
    waypoints: List[WaypointRequest]

class ProviderStatus(BaseModel):
    success: bool
    retrieved_at: str
    latest_forecast_time: Optional[str] = None
    error: Optional[str] = None

class WaypointLiveConditions(BaseModel):
    lat: float
    lon: float
    weather_status: ProviderStatus
    marine_status: ProviderStatus
    
    wind_speed_10m: Optional[float] = None
    wind_direction_10m: Optional[float] = None
    temperature_2m: Optional[float] = None
    precipitation: Optional[float] = None
    visibility: Optional[float] = None
    
    ocean_current_velocity: Optional[float] = None
    ocean_current_direction: Optional[float] = None
    wave_height: Optional[float] = None
    wave_direction: Optional[float] = None

class LiveEnvironmentResponse(BaseModel):
    waypoints: List[WaypointLiveConditions]
