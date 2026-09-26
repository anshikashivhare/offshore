import pytest
import asyncio
from app.services.routing.grid import Node, GridBuilder
from app.services.routing.astar import AStarRoutePlanner
from app.services.routing.validator import RouteValidator, route_validator
from app.models.vessel import Vessel
from app.models.enums import ObjectiveType
from app.schemas.route import RouteRequest
from global_land_mask import globe

@pytest.fixture
def planner():
    return AStarRoutePlanner(resolution=0.5)

import uuid
from datetime import datetime

@pytest.fixture
def vessel():
    return Vessel(vessel_id=uuid.uuid4(), cruising_speed=12.0, fuel_consumption=10.0)

def count_land_intersections(geometry_wkt: str) -> int:
    is_valid, msg, details = route_validator.validate_wkt_linestring(geometry_wkt, strict=False)
    return 0 if is_valid else 1

@pytest.mark.asyncio
async def test_ocean_to_ocean_no_land(planner, vessel):
    req = RouteRequest(
        vessel_id=uuid.uuid4(),
        origin="-50.0,-60.0",
        destination="-48.0,-60.0",
        departure_time=datetime.utcnow(),
        objective_type=ObjectiveType.FASTEST
    )
    route = await planner.plan_route(req, vessel, risk_grid={}, demo_mode=True)
    assert count_land_intersections(route.geometry) == 0

@pytest.mark.asyncio
async def test_route_blocked_by_land(planner, vessel):
    # Try to route directly through South America (e.g. from Pacific to Atlantic)
    req = RouteRequest(
        vessel_id=uuid.uuid4(),
        origin="-75.0,-45.0", # West of Chile
        destination="-65.0,-45.0", # East of Argentina
        departure_time=datetime.utcnow(),
        objective_type=ObjectiveType.FASTEST
    )
    # The A* should route AROUND South America, but since it's far, it might fail or take a long time
    # Let's use a smaller peninsula to test routing around it
    req2 = RouteRequest(
        vessel_id=uuid.uuid4(),
        origin="-65.0,-64.0", # West of Antarctic peninsula
        destination="-55.0,-64.0", # East of Antarctic peninsula
        departure_time=datetime.utcnow(),
        objective_type=ObjectiveType.FASTEST
    )
    route = await planner.plan_route(req2, vessel, risk_grid={}, demo_mode=True)
    assert count_land_intersections(route.geometry) == 0

@pytest.mark.asyncio
async def test_invalid_land_origin(planner, vessel):
    # Somewhere in the middle of Antarctica
    req = RouteRequest(
        vessel_id=uuid.uuid4(),
        origin="0.0,-85.0",
        destination="-55.0,-64.0",
        departure_time=datetime.utcnow(),
        objective_type=ObjectiveType.FASTEST
    )
    # To test the API snapping behavior directly, we just call the planner with the invalid origin
    snapped_origin = planner.grid_builder.snap_to_water(Node(-85.0, 0.0), max_radius_degrees=3.0)
    assert snapped_origin is None
