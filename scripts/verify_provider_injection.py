import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))
from app.services.orchestration.route_orchestrator import RouteOrchestrator
from app.schemas.route import RouteRequest
from app.models.vessel import Vessel
from app.models.enums import ObjectiveType

async def run_pipeline():
    print("--- 1. INITIALIZING ORCHESTRATOR ---")
    orchestrator = RouteOrchestrator(db_session=None)
    
    import uuid
    dummy_id = str(uuid.uuid4())
    req = RouteRequest(
        vessel_id=dummy_id,
        origin="-60.0,-60.0",
        destination="-61.0,-60.0",
        departure_time=datetime.now(timezone.utc),
        objective_type=ObjectiveType.FASTEST
    )
    
    # Create the vessel representation
    vessel = Vessel(
        vessel_id=uuid.UUID(dummy_id),
        vessel_name="Test Vessel",
        vessel_type="Icebreaker",
        max_speed=15.0,
        cruising_speed=12.0,
        draft_m=8.0,
        fuel_consumption=10.0
    )
    
    print("--- 2. EXECUTING A* ROUTE PLAN ---")
    try:
        route = await orchestrator.execute_route_plan(req, vessel)
        print("Success! Route generated:")
        print(f"Distance: {route.distance:.2f} NM")
        print(f"Travel Time: {route.travel_time:.2f} hours")
        print(f"Risk Status: {route.risk_data_status}")
        print(f"Validation: {'Passed' if route.land_avoidance_validated else 'Failed'}")
    except Exception as e:
        print(f"Route planning failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
