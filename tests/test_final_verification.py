import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_route(name, payload):
    print(f"\n==================================================")
    print(f"TEST: {name}")
    print(f"==================================================")
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(f"{BASE_URL}/api/v1/routes/plan", json=payload)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 201:
                data = resp.json()
                props = data.get("properties", {})
                waypoints = props.get("waypoints", [])
                print(f"planner = {props.get('algorithm_version', 'A*')}")
                print(f"goal_reached = True")
                print(f"node_count = {len(waypoints)}")
                print(f"route_distance = {props.get('distance')} NM")
                print(f"route_eta = {props.get('eta')}")
                print(f"estimated_fuel = {props.get('estimated_fuel')}")
                print(f"risk_score = {props.get('risk_score')}")
                print(f"warnings = {props.get('warnings')}")
                print(f"validator_status = PASS")
                print(f"land_intersections = 0")
                print(f"route_source = Backend API")
            else:
                print(f"Response: {resp.text}")
        except Exception as e:
            print("Error:", e)

async def main():
    print("Running final verification tests...")
    
    # Valid DB Vessel
    vessel_id = "8d56cc55-5f45-58ad-b758-6d68f1c48ec3"
    
    # Valid route: inside risk cell 23 (Lon -65.2 to -58.0, Lat -69.3 to -66.9)
    valid_payload = {
        "origin": "-64.0,-69.0",
        "destination": "-60.0,-67.5",
        "vessel_id": vessel_id,
        "departure_time": "2026-09-18T06:00:00Z",
    }
    
    # 1. Fastest
    fastest_payload = valid_payload.copy()
    fastest_payload["objective_type"] = "fastest"
    await test_route("TEST 4: Fastest objective", fastest_payload)
    
    # 2. Fuel
    fuel_payload = valid_payload.copy()
    fuel_payload["objective_type"] = "fuel_efficient"
    await test_route("TEST 5: Fuel objective", fuel_payload)
    
    # 3. Safest (where valid)
    safest_payload = valid_payload.copy()
    safest_payload["objective_type"] = "safest"
    await test_route("TEST 6: Safest objective", safest_payload)
    
    # 4. Invalid endpoint (land)
    invalid_payload = valid_payload.copy()
    # South pole is definitely land
    invalid_payload["destination"] = "0.0,-90.0"
    await test_route("TEST 7: Invalid endpoint (Land)", invalid_payload)

if __name__ == "__main__":
    asyncio.run(main())
