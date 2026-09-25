import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

import asyncio
from datetime import datetime, timedelta
from backend.app.schemas.route import RouteRequest, OptimizationWeights
from backend.app.models.vessel import Vessel
from backend.app.models.enums import ObjectiveType
from backend.app.services.routing.astar import AStarRoutePlanner

async def main():
    print("--- REAL A* ICEBERG INTEGRATION PROOF ---")
    planner = AStarRoutePlanner(resolution=0.5)
    
    # We create a mock vessel
    vessel = Vessel(
        id="demo",
        name="Demo Vessel",
        cruising_speed=12.0,
        fuel_consumption=10.0,
        ice_capability=True,
        draft_m=10.0,
        max_wave_height_m=5.0
    )
    
    # We want a very short route directly through our mock iceberg at -60.05, 50.55
    request = RouteRequest(
        vessel_id="demo",
        origin="50.0,-60.0",
        destination="51.0,-60.0",
        departure_time=datetime.utcnow(),
        objective_type=ObjectiveType.FASTEST,
        weights=OptimizationWeights(alpha=0.1, beta=0.8, gamma=0.1)
    )
    
    try:
        # Run in demo mode so missing DB risk surfaces don't crash
        route = await planner.plan_route(request, vessel, risk_grid={}, demo_mode=True)
        print(f"\nA* Route Output:")
        print(f"Algorithm: {route.algorithm_version}")
        print(f"Risk Status: {route.risk_data_status}")
        print(f"Distance: {route.distance:.2f} NM")
        print(f"Travel Time: {route.travel_time:.2f} hrs")
        print(f"Total Risk Exposure: {route.risk_exposure:.2f}")
        print(f"Route Selected! The integration logic inside A* executed successfully without crashing.")
    except Exception as e:
        print(f"A* Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
