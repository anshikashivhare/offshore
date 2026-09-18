import pytest
import math
from app.services.routing.cost import RouteScorer, CostCalculator
from app.models.vessel import Vessel
from app.services.routing.grid import Node
from app.schemas.route import OptimizationWeights

def test_vessel_speed_vectors():
    weights = OptimizationWeights()
    scorer = RouteScorer(weights, CostCalculator())
    
    vessel = Vessel(vessel_id="123", cruising_speed=12.0, fuel_consumption=10.0)
    
    # Heading North (0 rad)
    current_node = Node(lat=-60.0, lon=-60.0)
    neighbor_node = Node(lat=-59.0, lon=-60.0)
    
    # 1. Pure tail current (flowing North, 0 deg)
    env_tail = {
        "ocean_current_velocity": 3.0,
        "ocean_current_direction": 0.0,
        "wind_speed_10m": 0.0,
        "wave_height": 0.0
    }
    sog_tail = scorer.get_effective_speed(current_node, neighbor_node, vessel, env_tail)
    assert abs(sog_tail - 15.0) < 0.1
    
    # 2. Pure head current (flowing South, 180 deg)
    env_head = {
        "ocean_current_velocity": 3.0,
        "ocean_current_direction": 180.0,
        "wind_speed_10m": 0.0,
        "wave_height": 0.0
    }
    sog_head = scorer.get_effective_speed(current_node, neighbor_node, vessel, env_head)
    assert abs(sog_head - 9.0) < 0.1
    
    # 3. Pure cross current (flowing East, 90 deg)
    env_cross = {
        "ocean_current_velocity": 3.0,
        "ocean_current_direction": 90.0,
        "wind_speed_10m": 0.0,
        "wave_height": 0.0
    }
    sog_cross = scorer.get_effective_speed(current_node, neighbor_node, vessel, env_cross)
    # Cosine of 90 is 0, so no along-track speed change
    assert abs(sog_cross - 12.0) < 0.1
    
    # 4. Severe headwind and waves
    env_weather = {
        "ocean_current_velocity": 0.0,
        "ocean_current_direction": 0.0,
        "wind_speed_10m": 40.0,
        "wind_direction_10m": 180.0, # Blowing from South (headwind)
        "wave_height": 3.0
    }
    sog_weather = scorer.get_effective_speed(current_node, neighbor_node, vessel, env_weather)
    # headwind penalty: 40 * 0.05 = 2.0
    # wave penalty: 3.0 * 0.5 = 1.5
    # total penalty = 3.5
    # 12 - 3.5 = 8.5
    assert abs(sog_weather - 8.5) < 0.1
