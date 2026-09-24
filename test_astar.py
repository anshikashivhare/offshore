import sys
from pathlib import Path
_root = str(Path(__file__).resolve().parents[0] / "backend")
if _root not in sys.path:
    sys.path.insert(0, _root)

import asyncio
from datetime import datetime
from app.services.routing.astar import AStarRoutePlanner
from app.services.routing.grid import Node
from app.schemas.route import RouteRequest, OptimizationWeights
from app.models.vessel import Vessel
from app.models.enums import ObjectiveType
from app.schemas.route import RiskGridData

async def main():
    planner = AStarRoutePlanner(resolution=0.5)
    start = Node(lat=-67.5695, lon=-68.1250)
    goal = Node(lat=-34.3688, lon=151.2093)
    
    req = RouteRequest(
        vessel_id="3a92b8d0-5e8a-4c28-8d4e-1b7f2c69d4a1",
        origin="-68.1250,-67.5695",
        destination="151.2093,-34.3688",
        departure_time=datetime.utcnow(),
        objective_type=ObjectiveType.FASTEST
    )
    import uuid
    vessel = Vessel(vessel_id=uuid.UUID("3a92b8d0-5e8a-4c28-8d4e-1b7f2c69d4a1"), vessel_name="Test", vessel_type="Cargo", cruising_speed=12.0, fuel_consumption=25.0)
    
    print("Running A* from Rothera to Sydney...")
    try:
        route = await planner.plan_route(
            vessel=vessel,
            request=req,
            risk_grid=RiskGridData(cells={}, status="UNAVAILABLE", ml_status="UNAVAILABLE", warnings=[]),
            demo_mode=False
        )
        print("Success!")
    except Exception as e:
        print("Failed:", e)

if __name__ == "__main__":
    asyncio.run(main())
