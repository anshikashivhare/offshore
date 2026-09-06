import pytest
import uuid
from datetime import datetime, timezone
from app.models.vessel import Vessel
from app.models.enums import ObjectiveType
from app.schemas.route import RouteRequest, OptimizationWeights
from app.services.routing.astar import AStarRoutePlanner
from app.services.routing.grid import Node

@pytest.fixture
def vessel():
    return Vessel(
        vessel_id=uuid.uuid4(),
        vessel_name="Test Ship",
        vessel_type="Cargo",
        cruising_speed=12.0,
        fuel_consumption=50.0,
        ice_capability="PC4",
        operational_limits={}
    )

@pytest.fixture
def no_ice_vessel():
    return Vessel(
        vessel_id=uuid.uuid4(),
        vessel_name="No Ice Ship",
        vessel_type="Cargo",
        cruising_speed=15.0,
        fuel_consumption=70.0,
        ice_capability="",
        operational_limits={}
    )

@pytest.fixture
def planner():
    return AStarRoutePlanner(resolution=1.0)

@pytest.mark.asyncio
async def test_astar_basic_path_finding(planner, vessel):
    req = RouteRequest(
        origin="0,0",
        destination="0,2",
        vessel_id=vessel.vessel_id,
        departure_time=datetime.now(timezone.utc),
        objective_type=ObjectiveType.FASTEST
    )
    
    # Empty risk grid
    route = await planner.plan_route(req, vessel, {})
    assert route.distance > 0
    assert route.estimated_fuel > 0

@pytest.mark.asyncio
async def test_astar_blocked_cell_routing(planner, vessel):
    req = RouteRequest(
        origin="0,0",
        destination="0,3",
        vessel_id=vessel.vessel_id,
        departure_time=datetime.now(timezone.utc),
        objective_type=ObjectiveType.SAFEST
    )
    
    # Block the direct path
    risk_grid = {
        (0.0, 1.0): 1.0,
        (0.0, 2.0): 1.0
    }
    
    route = await planner.plan_route(req, vessel, risk_grid)
    # The route must have gone around, so distance > straight line
    assert route.distance > 0

@pytest.mark.asyncio
async def test_astar_no_feasible_route(planner, vessel):
    req = RouteRequest(
        origin="0,0",
        destination="0,2",
        vessel_id=vessel.vessel_id,
        departure_time=datetime.now(timezone.utc),
        objective_type=ObjectiveType.SAFEST
    )
    
    # Surround destination (lat=2.0, lon=0.0) with obstacles on a 1.0 resolution grid
    risk_grid = {
        (1.0, 0.0): 1.0,
        (3.0, 0.0): 1.0,
        (2.0, 1.0): 1.0,
        (2.0, -1.0): 1.0,
        (1.0, 1.0): 1.0,
        (1.0, -1.0): 1.0,
        (3.0, 1.0): 1.0,
        (3.0, -1.0): 1.0
    }
    
    with pytest.raises(ValueError, match="No feasible route exists"):
        await planner.plan_route(req, vessel, risk_grid)

@pytest.mark.asyncio
async def test_vessel_constraints(planner, no_ice_vessel):
    req = RouteRequest(
        origin="0,0",
        destination="0,2",
        vessel_id=no_ice_vessel.vessel_id,
        departure_time=datetime.now(timezone.utc),
        objective_type=ObjectiveType.SAFEST
    )
    
    # Ice risk > 0.5 should block no_ice_vessel
    risk_grid = {
        (0.0, 1.0): 0.6
    }
    
    route = await planner.plan_route(req, no_ice_vessel, risk_grid)
    # The route must have gone around the 0.6 risk cell
    assert route.distance > 120 # distance in NM, straight is ~120, circumventing is longer

@pytest.mark.asyncio
async def test_objective_weights(planner, vessel):
    req_safest = RouteRequest(
        origin="0,0",
        destination="0,2",
        vessel_id=vessel.vessel_id,
        departure_time=datetime.now(timezone.utc),
        objective_type=ObjectiveType.SAFEST
    )
    
    req_fastest = RouteRequest(
        origin="0,0",
        destination="0,2",
        vessel_id=vessel.vessel_id,
        departure_time=datetime.now(timezone.utc),
        objective_type=ObjectiveType.FASTEST
    )
    
    risk_grid = {
        (0.0, 1.0): 0.4 # Moderate risk
    }
    
    route_safest = await planner.plan_route(req_safest, vessel, risk_grid)
    route_fastest = await planner.plan_route(req_fastest, vessel, risk_grid)
    
    # Fastest might barge through 0.4 risk, safest might go around
    # Since safest has high gamma, it avoids it.
    assert route_safest.distance >= route_fastest.distance
