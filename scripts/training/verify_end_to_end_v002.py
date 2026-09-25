import asyncio
from pathlib import Path
import sys
from datetime import datetime

# Setup path for backend
_root = str(Path(__file__).resolve().parents[0])
if _root not in sys.path:
    sys.path.insert(0, _root)

from app.services.forecasting.ml_forecaster import MLForecaster
from app.services.routing.astar import AStarRoutePlanner
from app.services.routing.grid import Node

async def run_verification():
    print("--- PHASE 1: DIRECT V002 INFERENCE ---")
    forecaster = MLForecaster()
    try:
        res = await forecaster.generate_predictions(horizons_hours=[24])
        print("V002 Forecast via MLForecaster executed.")
    except Exception as e:
        print("MLForecaster failed:", e)

    print("\n--- PHASE 4 & 5 & 6 & 7: ROUTING AND COST CAUSALITY ---")
    planner = AStarRoutePlanner()
    
    class DummyVessel:
        cruising_speed = 12.0
        fuel_consumption = 1.0
        def __init__(self):
            pass
            
    from app.models.enums import ObjectiveType
    import uuid

    class DummyRequest:
        objective_type = ObjectiveType.FASTEST
        weights = None
        origin = "155.0,-35.0" # Offshore Sydney (Tasman Sea)
        destination = "-65.0,-65.0" # Drake Passage/Bellingshausen Sea
        departure_time = datetime.utcnow()
        vessel_id = str(uuid.uuid4())
        
    dummy_vessel = DummyVessel()
    dummy_req = DummyRequest()
    
    try:
        print("Attempting Sydney -> Rothera")
        path_s2r = await planner.plan_route(dummy_req, dummy_vessel, risk_grid={}, demo_mode=True)
        print("Success! Route found.")
    except Exception as e:
        print("Routing failed:", e)

    try:
        print("Attempting Rothera -> Sydney")
        dummy_req_rev = DummyRequest()
        dummy_req_rev.origin = "-65.0,-65.0"
        dummy_req_rev.destination = "155.0,-35.0"
        dummy_req_rev.departure_time = datetime.utcnow()
        path_r2s = await planner.plan_route(dummy_req_rev, dummy_vessel, risk_grid={}, demo_mode=True)
        print("Success! Reverse route found.")
    except Exception as e:
        print("Reverse Routing failed:", e)

if __name__ == "__main__":
    asyncio.run(run_verification())
