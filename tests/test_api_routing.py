import asyncio
from pathlib import Path
import sys

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
        # Pass dummy kwargs to ensure it runs
        res = await forecaster.generate_predictions(horizons_hours=[24])
        print("V002 Forecast via MLForecaster executed.")
    except Exception as e:
        print("MLForecaster failed:", e)

    print("\n--- PHASE 4 & 5 & 6 & 7: ROUTING AND COST CAUSALITY ---")
    planner = AStarRoutePlanner()
    
    # Sydney to Rothera
    sydney = Node(-33.8688, 151.2093)
    rothera = Node(-67.57, -68.12)
    
    try:
        print("Attempting Sydney -> Rothera")
        path_s2r = planner.plan_route(sydney, rothera)
        print(f"Success! Route found. Nodes: {len(path_s2r)}")
    except Exception as e:
        print("Routing failed:", e)

if __name__ == "__main__":
    asyncio.run(run_verification())
