import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from app.services.routing.astar import AStarRoutePlanner
from app.services.routing.grid import Node
from app.models.vessel import Vessel
from app.schemas.route import RouteRequest
from app.models.enums import ObjectiveType

# Mock the global forecast grid
class MockForecastGrid:
    def __init__(self):
        self.storm_active = False

    async def prefetch_corridor(self, waypoints):
        pass

    def get_conditions(self, lat, lon, target_time):
        # Default benign conditions
        conditions = {
            "ocean_current_velocity": 0.0,
            "ocean_current_direction": 0.0,
            "wind_speed_10m": 10.0,
            "wind_direction_10m": 90.0,
            "wave_height": 0.5
        }
        
        # Introduce a severe storm at (lat=-63.0, lon=-56.0) 24 hours into the voyage
        # If storm_active is True, it blocks the direct path
        if self.storm_active:
            hours_from_start = (target_time - datetime(2026, 9, 19, 12, tzinfo=timezone.utc)).total_seconds() / 3600.0
            
            # The storm is located near -63, -56 and arrives between hour 12 and 48
            if 12 <= hours_from_start <= 48:
                if abs(lat - (-63.0)) <= 2.0 and abs(lon - (-56.0)) <= 2.0:
                    conditions["wave_height"] = 8.0 # This triggers the hard constraint (max 5.0)
                    conditions["wind_speed_10m"] = 50.0

        return conditions

@pytest.fixture
def mock_vessel():
    return Vessel(
        vessel_id="123e4567-e89b-12d3-a456-426614174001",
        cruising_speed=12.0,
        fuel_consumption=10.0
    )

@pytest.fixture
def mock_request():
    return RouteRequest(
        origin="-60.0,-65.0", # lon, lat
        destination="-55.0,-60.0",
        vessel_id="123e4567-e89b-12d3-a456-426614174001",
        departure_time=datetime(2026, 9, 19, 12, 0, tzinfo=timezone.utc),
        objective_type=ObjectiveType.SAFEST
    )

@pytest.mark.asyncio
async def test_dynamic_storm_detour(mock_vessel, mock_request, monkeypatch):
    """
    Test that a time-evolving storm changes the route selection.
    """
    planner = AStarRoutePlanner(resolution=1.0)
    mock_grid = MockForecastGrid()
    
    # Patch the global instance
    import app.services.environment.forecast_grid
    monkeypatch.setattr(app.services.environment.forecast_grid, "global_forecast_grid", mock_grid)
    
    # Run 1: No Storm
    mock_grid.storm_active = False
    route_no_storm = await planner.plan_route(mock_request, mock_vessel, risk_grid={})
    
    # Run 2: Storm Active
    mock_grid.storm_active = True
    route_with_storm = await planner.plan_route(mock_request, mock_vessel, risk_grid={})
    
    # The routes must be different
    assert route_no_storm.geometry != route_with_storm.geometry
    
    # The route with the storm should be longer due to the detour
    assert route_with_storm.distance > route_no_storm.distance
    
    # Print for evidence report
    print(f"No Storm Cost (Distance): {route_no_storm.distance}")
    print(f"No Storm Geometry: {route_no_storm.geometry}")
    print(f"With Storm Cost (Distance): {route_with_storm.distance}")
    print(f"With Storm Geometry: {route_with_storm.geometry}")
