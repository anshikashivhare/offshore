import asyncio
from app.schemas.route import RouteRequest
from app.services.routing.astar import AStarRoutePlanner
from app.models.vessel import Vessel
import datetime
import uuid

async def test():
    planner = AStarRoutePlanner(resolution=0.5)
    request = RouteRequest(
        vessel_id=uuid.uuid4(),
        origin="72.8,18.9", # Mumbai
        destination="110.5,-66.3", # Casey
        departure_time=datetime.datetime.now(datetime.timezone.utc),
        objective_type="fastest"
    )
    vessel = Vessel(vessel_id=uuid.uuid4(), cruising_speed=12.0, fuel_consumption=2000.0)
    try:
        route = await planner.plan_route(request, vessel, {})
        print("Success! Distance:", route.distance)
        print("Geometry:", route.geometry[:100], "...")
    except Exception as e:
        print("Failed:", str(e))

asyncio.run(test())
