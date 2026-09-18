import asyncio
import httpx
from datetime import datetime, timezone
import math
from typing import Dict, Any, Optional, Tuple

from app.schemas.environment_live import (
    WaypointRequest, LiveEnvironmentResponse, WaypointLiveConditions, ProviderStatus
)

# Simple in-memory cache to prevent spamming Open-Meteo
# Key: (lat, lon, hour_timestamp, api_type) -> Value: (cached_at_datetime, result_dict)
_cache: Dict[Tuple[float, float, str, str], Tuple[datetime, Any]] = {}

CACHE_TTL_SECONDS = 60

async def _fetch_openmeteo(
    client: httpx.AsyncClient, 
    lat: float, 
    lon: float, 
    eta: Optional[datetime],
    is_marine: bool
) -> Tuple[ProviderStatus, Dict[str, float]]:
    
    # Determine the target hour string for caching
    target_dt = eta if eta else datetime.now(timezone.utc)
    target_hour = target_dt.strftime("%Y-%m-%dT%H:00")
    
    api_type = "marine" if is_marine else "weather"
    lat_round = round(lat, 2)
    lon_round = round(lon, 2)
    cache_key = (lat_round, lon_round, target_hour, api_type)
    
    now_utc = datetime.now(timezone.utc)
    
    # Check cache
    if cache_key in _cache:
        cached_at, cached_result = _cache[cache_key]
        if (now_utc - cached_at).total_seconds() < CACHE_TTL_SECONDS:
            return cached_result
            
    # Prepare API Request
    try:
        if is_marine:
            url = "https://marine-api.open-meteo.com/v1/marine"
            params = {
                "latitude": lat,
                "longitude": lon,
                "hourly": "ocean_current_velocity,ocean_current_direction,wave_height,wave_direction",
                "timezone": "UTC"
            }
        else:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "hourly": "wind_speed_10m,wind_direction_10m,temperature_2m,precipitation,visibility",
                "timezone": "UTC"
            }
            
        response = await client.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        # Find the index for the target hour
        times = data.get("hourly", {}).get("time", [])
        if not times:
            raise ValueError("No hourly time array found in response")
            
        target_idx = -1
        # Fallback to nearest or just exact string match
        if target_hour in times:
            target_idx = times.index(target_hour)
        else:
            # Fallback to the first available if not found (or closest)
            target_idx = 0
            
        latest_forecast_time = times[target_idx]
        
        extracted_vars = {}
        for key, values in data.get("hourly", {}).items():
            if key == "time":
                continue
            val = values[target_idx]
            if val is not None:
                extracted_vars[key] = float(val)
                
        status = ProviderStatus(
            success=True,
            retrieved_at=now_utc.isoformat(),
            latest_forecast_time=latest_forecast_time,
            error=None
        )
        
        result = (status, extracted_vars)
        _cache[cache_key] = (now_utc, result)
        return result
        
    except Exception as e:
        # On failure, return what we can
        # If we have a stale cache, return it with a stale flag maybe?
        # The user requested: "A failed poll preserves the last successful data while displaying a stale-data warning."
        if cache_key in _cache:
            _, stale_result = _cache[cache_key]
            # Mutate to show it's stale/error but keep data
            stale_status, stale_vars = stale_result
            # We don't update retrieved_at so it shows as old
            new_status = ProviderStatus(
                success=False, # It failed this time
                retrieved_at=stale_status.retrieved_at, 
                latest_forecast_time=stale_status.latest_forecast_time,
                error=f"Stale data fallback (Fetch error: {str(e)})"
            )
            return new_status, stale_vars
            
        status = ProviderStatus(
            success=False,
            retrieved_at=now_utc.isoformat(),
            error=str(e)
        )
        return status, {}

async def fetch_live_environment_for_waypoints(waypoints: list[WaypointRequest]) -> LiveEnvironmentResponse:
    async with httpx.AsyncClient() as client:
        tasks = []
        for wp in waypoints:
            tasks.append(_fetch_openmeteo(client, wp.lat, wp.lon, wp.eta, is_marine=False))
            tasks.append(_fetch_openmeteo(client, wp.lat, wp.lon, wp.eta, is_marine=True))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        out_waypoints = []
        for i, wp in enumerate(waypoints):
            weather_res = results[i*2]
            marine_res = results[i*2 + 1]
            
            # Handle if gather threw an exception itself (should be caught inside _fetch_openmeteo usually)
            if isinstance(weather_res, Exception):
                w_status = ProviderStatus(success=False, retrieved_at=datetime.now(timezone.utc).isoformat(), error=str(weather_res))
                w_vars = {}
            else:
                w_status, w_vars = weather_res
                
            if isinstance(marine_res, Exception):
                m_status = ProviderStatus(success=False, retrieved_at=datetime.now(timezone.utc).isoformat(), error=str(marine_res))
                m_vars = {}
            else:
                m_status, m_vars = marine_res
                
            out_waypoints.append(WaypointLiveConditions(
                lat=wp.lat,
                lon=wp.lon,
                weather_status=w_status,
                marine_status=m_status,
                wind_speed_10m=w_vars.get("wind_speed_10m"),
                wind_direction_10m=w_vars.get("wind_direction_10m"),
                temperature_2m=w_vars.get("temperature_2m"),
                precipitation=w_vars.get("precipitation"),
                visibility=w_vars.get("visibility"),
                ocean_current_velocity=m_vars.get("ocean_current_velocity"),
                ocean_current_direction=m_vars.get("ocean_current_direction"),
                wave_height=m_vars.get("wave_height"),
                wave_direction=m_vars.get("wave_direction"),
            ))
            
        return LiveEnvironmentResponse(waypoints=out_waypoints)
