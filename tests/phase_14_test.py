import asyncio
import json
import httpx
from datetime import datetime
import sys

routes = {
    "Rothera -> Sydney": {"origin": "-68.125,-67.5695", "destination": "151.2093,-34.3688"},
    "Sydney -> Rothera": {"origin": "151.2093,-34.3688", "destination": "-68.125,-67.5695"}
}

async def run_route(name, coords):
    print(f"Running {name}...")
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                "http://127.0.0.1:8000/api/v1/routes/compare",
                json={
                    "vessel_id": "3a92b8d0-5e8a-4c28-8d4e-1b7f2c69d4a1",
                    "origin": coords["origin"],
                    "destination": coords["destination"],
                    "departure_time": datetime.utcnow().isoformat() + "Z",
                    "objective_type": "fastest"
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                props = data.get("recommended_route", {}).get("properties", {})
                print(f"  SUCCESS: {name}")
                print(f"    distance_nm: {props.get('distance_nm')}")
                print(f"    eta: {props.get('eta')}")
                print(f"    node_count: {props.get('node_count')}")
                print(f"    risk_score: {props.get('risk_score')}")
                print(f"    ml_prediction_status: {props.get('ml_prediction_status')}")
                print(f"    land_intersections: {props.get('land_intersections')}")
                
                geom = data.get("recommended_route", {}).get("geometry", {})
                waypoints = geom.get("coordinates", [])
                print(f"    first 5 waypoints: {waypoints[:5]}")
                print(f"    middle waypoint: {waypoints[len(waypoints)//2] if waypoints else 'None'}")
                print(f"    last 5 waypoints: {waypoints[-5:]}")
            else:
                print(f"  FAILED: {name} - HTTP {resp.status_code}")
                print(f"    {resp.text}")
    except Exception as e:
        print(f"  ERROR: {name} - {e}")

async def main():
    for name, coords in routes.items():
        await run_route(name, coords)

if __name__ == "__main__":
    asyncio.run(main())
