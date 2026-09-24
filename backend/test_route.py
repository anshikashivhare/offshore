import asyncio
from app.schemas.route import RouteRequest
from app.models.enums import ObjectiveType
from app.services.routing.astar import AStarRoutePlanner
from app.models.vessel import Vessel
from global_land_mask import globe
from app.services.routing.grid import Node

async def main():
    request = RouteRequest(
        vessel_id='00000000-0000-0000-0000-000000000000', 
        origin='165,-77.8', 
        destination='-60,-60', 
        objective_type=ObjectiveType.FASTEST, 
        departure_time='2026-09-13T12:00:00Z'
    )
    planner = AStarRoutePlanner(resolution=0.5)
    vessel = Vessel(
        vessel_id='00000000-0000-0000-0000-000000000000', 
        vessel_name='Demo Explorer', 
        vessel_type='Research', 
        ice_capability='PC3', 
        cruising_speed=12.0, 
        fuel_consumption=2000.0
    )

    origin_node = Node(lat=-77.8, lon=165)
    dest_node = Node(lat=-60, lon=-60)
    snapped_origin = planner.grid_builder.snap_to_water(origin_node, 2.0)
    snapped_dest = planner.grid_builder.snap_to_water(dest_node, 2.0)
    if snapped_origin: 
        request.origin = f'{snapped_origin.lon},{snapped_origin.lat}'
    if snapped_dest: 
        request.destination = f'{snapped_dest.lon},{snapped_dest.lat}'

    try:
        res = await planner.plan_route(request, vessel, {}, demo_mode=True)
        land_nodes = []
        for wp in res.waypoints:
            if globe.is_land(wp.lat, wp.lon):
                land_nodes.append((wp.lat, wp.lon))
        print(f'Land waypoints found: {len(land_nodes)}')
        if land_nodes:
            print(land_nodes[:5])
    except Exception as e:
        print(e)

if __name__ == '__main__':
    asyncio.run(main())
