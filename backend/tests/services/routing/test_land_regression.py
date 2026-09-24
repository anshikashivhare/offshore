import pytest
import math
from app.services.routing.grid import GridBuilder, Node
from app.services.routing.astar import AStarRoutePlanner
from app.models.enums import ObjectiveType
from app.schemas.route import RouteRequest
from app.models.vessel import Vessel
from global_land_mask import globe

def test_antimeridian_interpolation_regression():
    """Verify that neighbors crossing the antimeridian interpolate the shortest path and don't wrap around the globe."""
    grid_builder = GridBuilder(resolution=1.0)
    # Start at 179.5
    start_node = Node(lat=-60.0, lon=179.5)
    neighbors = grid_builder.get_neighbors(start_node)
    
    # One of the neighbors should be across the antimeridian
    # dlon = 1.0 -> new_lon = 180.5 -> wraps to -179.5
    wrapped_node = next((n for n in neighbors if n.lat == -60.0 and n.lon == -179.5), None)
    
    # If the segment check wraps around the globe backwards (359 degrees), it will hit land
    # and the neighbor will be rejected. 
    # If it correctly interpolates across the 1.0 degree gap, it will stay in water and be accepted.
    assert wrapped_node is not None, "Neighbor across antimeridian was rejected, likely due to incorrect interpolation crossing land."

@pytest.mark.asyncio
async def test_route_line_segments_no_land():
    """
    Verify that EVERY waypoint in the final route is on navigable water.
    Verify that the LineString segments between consecutive waypoints do NOT cross land.
    """
    planner = AStarRoutePlanner(resolution=0.5)
    
    # Request a route that goes near land. 
    # Let's route from one side of the Antarctic Peninsula to the other, or any known land obstacle.
    request = RouteRequest(
        vessel_id='00000000-0000-0000-0000-000000000000',
        origin='-59,-62', # West of peninsula
        destination='-55,-65', # East of peninsula
        objective_type=ObjectiveType.SHORTEST,
        departure_time='2026-09-13T12:00:00Z'
    )
    
    vessel = Vessel(
        vessel_id='00000000-0000-0000-0000-000000000000',
        vessel_name='Demo Explorer',
        vessel_type='Research',
        ice_capability='PC3',
        cruising_speed=12.0,
        fuel_consumption=2000.0
    )
    
    route_create = await planner.plan_route(request, vessel, {}, demo_mode=True)
    
    # 1. Verify all waypoints are in water (and they are grid aligned)
    for wp in route_create.waypoints:
        assert not globe.is_land(wp.lat, wp.lon), f"Waypoint at {wp.lat}, {wp.lon} is on land!"
        
    # 2. Verify segments between consecutive waypoints don't cross land
    # Re-use segment sampling logic to verify
    for i in range(len(route_create.waypoints) - 1):
        wp1 = route_create.waypoints[i]
        wp2 = route_create.waypoints[i + 1]
        
        dlat = wp2.lat - wp1.lat
        dlon = wp2.lon - wp1.lon
        if dlon > 180: dlon -= 360
        elif dlon < -180: dlon += 360
            
        dist_deg = math.sqrt(dlat**2 + dlon**2)
        samples = max(5, int(dist_deg / 0.05))
        
        for j in range(0, samples + 1):
            t = j / float(samples)
            test_lat = wp1.lat + t * dlat
            test_lon = wp1.lon + t * dlon
            if test_lon > 180: test_lon -= 360
            elif test_lon < -180: test_lon += 360
                
            assert not globe.is_land(test_lat, test_lon), f"Segment from {wp1.lat},{wp1.lon} to {wp2.lat},{wp2.lon} crosses land at {test_lat},{test_lon}!"
