import asyncio
import httpx
from datetime import datetime, timezone, timedelta
import math
from typing import Dict, Any, List, Tuple
from app.services.routing.grid import Node
from app.schemas.environment_live import ProviderStatus

class ForecastGrid:
    def __init__(self):
        # keyed by (round(lat, 1), round(lon, 1))
        # value is a dict keyed by hour string, e.g. "2026-09-18T12:00"
        self.data: Dict[Tuple[float, float], Dict[str, Dict[str, float]]] = {}
        
    def _get_nearest_cache_key(self, lat: float, lon: float) -> Tuple[float, float]:
        return (round(lat, 1), round(lon, 1))
        
    def _get_nearest_time_key(self, target_time: datetime) -> str:
        # Snap to nearest 3-hour bucket
        hour = target_time.hour
        bucket_hour = (hour // 3) * 3
        bucket_time = target_time.replace(hour=bucket_hour, minute=0, second=0, microsecond=0)
        return bucket_time.strftime("%Y-%m-%dT%H:00")

    def get_conditions(self, lat: float, lon: float, target_time: datetime) -> Dict[str, float]:
        """Returns conditions for the nearest spatial point and 3-hour time bucket"""
        sp_key = self._get_nearest_cache_key(lat, lon)
        t_key = self._get_nearest_time_key(target_time)
        
        if sp_key not in self.data:
            return {}
            
        time_series = self.data[sp_key]
        if t_key not in time_series:
            # Fallback to nearest available or return empty
            return {}
            
        return time_series[t_key]
        
    async def prefetch_corridor(self, waypoints: List[Node]):
        """
        Prefetches data for a downsampled set of waypoints representing the corridor.
        We will request a 14-day horizon.
        """
        async with httpx.AsyncClient() as client:
            tasks = []
            
            # Downsample to avoid hammering the API
            # For a 5000 NM voyage, we might have 10,000 nodes.
            # Just sample every 50th node.
            sampled = waypoints[::50]
            if waypoints[-1] not in sampled:
                sampled.append(waypoints[-1])
                
            for node in sampled:
                tasks.append(self._fetch_point(client, node.lat, node.lon))
                
            # Batch in 10s to avoid rate limit
            for i in range(0, len(tasks), 10):
                batch = tasks[i:i+10]
                await asyncio.gather(*batch, return_exceptions=True)
                
    async def _fetch_point(self, client: httpx.AsyncClient, lat: float, lon: float):
        sp_key = self._get_nearest_cache_key(lat, lon)
        
        url_w = "https://api.open-meteo.com/v1/forecast"
        params_w = {
            "latitude": sp_key[0],
            "longitude": sp_key[1],
            "hourly": "wind_speed_10m,wind_direction_10m,wave_height",
            "timezone": "UTC",
            "forecast_days": 14
        }
        
        url_m = "https://marine-api.open-meteo.com/v1/marine"
        params_m = {
            "latitude": sp_key[0],
            "longitude": sp_key[1],
            "hourly": "ocean_current_velocity,ocean_current_direction,wave_height,wave_direction",
            "timezone": "UTC",
            "forecast_days": 14
        }
        
        try:
            res_w = await client.get(url_w, params=params_w, timeout=10.0)
            res_m = await client.get(url_m, params=params_m, timeout=10.0)
            
            data_w = res_w.json().get("hourly", {})
            data_m = res_m.json().get("hourly", {})
            
            times = data_w.get("time", [])
            
            point_data = {}
            for i, t in enumerate(times):
                try:
                    # Only store every 3 hours
                    dt = datetime.strptime(t, "%Y-%m-%dT%H:%M")
                    if dt.hour % 3 != 0:
                        continue
                        
                    t_key = self._get_nearest_time_key(dt)
                    point_data[t_key] = {
                        "wind_speed_10m": data_w.get("wind_speed_10m", [])[i],
                        "wind_direction_10m": data_w.get("wind_direction_10m", [])[i],
                        "ocean_current_velocity": data_m.get("ocean_current_velocity", [])[i] if data_m.get("ocean_current_velocity") else 0.0,
                        "ocean_current_direction": data_m.get("ocean_current_direction", [])[i] if data_m.get("ocean_current_direction") else 0.0,
                        "wave_height": data_m.get("wave_height", [])[i] if data_m.get("wave_height") else data_w.get("wave_height", [])[i],
                    }
                except (IndexError, TypeError, ValueError):
                    continue
                    
            self.data[sp_key] = point_data
            
        except Exception as e:
            print(f"Failed to fetch grid point {sp_key}: {e}")

global_forecast_grid = ForecastGrid()
