import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))

import asyncio
from datetime import datetime
from backend.app.schemas.route import RouteRequest, OptimizationWeights
from backend.app.models.vessel import Vessel
from backend.app.models.enums import ObjectiveType
from backend.app.services.routing.astar import AStarRoutePlanner

async def run_case(case_name, candidate_icebergs):
    planner = AStarRoutePlanner(resolution=0.5)
    vessel = Vessel(
        id="demo", name="Demo Vessel", cruising_speed=12.0, fuel_consumption=10.0,
        ice_capability=True, draft_m=10.0, max_wave_height_m=5.0
    )
    request = RouteRequest(
        vessel_id="demo", origin="50.0,-60.0", destination="52.0,-60.0",
        departure_time=datetime.utcnow(), objective_type=ObjectiveType.FASTEST,
        weights=OptimizationWeights(alpha=0.1, beta=0.8, gamma=0.1)
    )
    try:
        route = await planner.plan_route(request, vessel, risk_grid={}, demo_mode=True, candidate_icebergs=candidate_icebergs)
        print(f"\n--- {case_name} ---")
        print(f"Distance: {route.distance:.2f} NM")
        print(f"Travel Time: {route.travel_time:.2f} hrs")
        print(f"Total Risk Exposure: {route.risk_exposure:.2f}")
        print(f"Path Edges Evaluated: {len(route.waypoints)}")
        return route
    except Exception as e:
        print(f"\n--- {case_name} ---")
        print(f"A* Error: {e}")
        return None

async def main():
    print("========================================")
    print("ACTUAL CAUSAL A* ROUTE-SELECTION TEST")
    print("========================================")
    
    # CASE A: Iceberg Risk Disabled (No candidates passed in)
    await run_case("CASE A: ICEBERG RISK DISABLED", [])
    
    # CASE B: Iceberg Risk Enabled
    # We place an iceberg exactly in the direct path at 51.0, -60.0
    # The LSTM pred will drift it slightly, but uncertainty will block the edge.
    ice = {"iceberg_id": "demo-hazard", "lat": -60.0, "lon": 51.0, "source": "synthetic_demo"}
    await run_case("CASE B: ICEBERG RISK ENABLED", [ice])

if __name__ == "__main__":
    asyncio.run(main())
