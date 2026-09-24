import asyncio
import time
from app.services.routing.astar import AStarRoutePlanner
from app.schemas.route import RouteRequest
from app.models.vessel import Vessel
from datetime import datetime

async def main():
    planner = AStarRoutePlanner()
    req = RouteRequest(
        vessel_id="3a92b8d0-5e8a-4c28-8d4e-1b7f2c69d4a1",
        origin="151.2093,-34.3688", # Sydney
        destination="-68.125,-67.5695", # Rothera
        departure_time=datetime.utcnow()
    )
    class MockVessel:
        def __init__(self):
            self.vessel_id = req.vessel_id
            self.draft_m = 8.0
            self.cruising_speed = 12.0
            self.ice_capability = True
            self.fuel_consumption = 5.0
            
    vessel = MockVessel()
    
    print("Starting planner...")
    start_time = time.time()
    try:
        route = await planner.plan_route(req, vessel, demo_mode=True)
        print(f"Success in {time.time() - start_time:.2f}s!")
        print(route.distance, "NM")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
