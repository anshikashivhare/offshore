import asyncio
import httpx
import time
import json

async def run_test():
    url = "http://localhost:8000/api/v1/routes/plan"
    payload = {
        "vessel_id": "848e0cd9-bde8-48b8-b4b9-8e4af900bbfb",
        "origin": "-68.13,-67.57",
        "destination": "72.8,18.9",
        "departure_time": "2026-09-19T06:00:00Z",
        "objective_type": "fastest"
    }

    print("Testing route from Rothera (-68.13, -67.57) to Mumbai (72.8, 18.9)...")
    start_time = time.time()
    
    # Use a large timeout because AStar across the globe takes 60-90 seconds
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(url, json=payload)
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                print(f"SUCCESS! Status: {response.status_code}")
                print(f"Time taken: {end_time - start_time:.2f} seconds")
                print(f"Distance: {data.get('distance_nm', 'N/A')} NM")
                print(f"Route origin: {data.get('origin')}")
                print(f"Route destination: {data.get('destination')}")
                
                geometry = data.get('geometry', '')
                if geometry:
                    points = geometry.replace("LINESTRING(", "").replace(")", "").split(",")
                    print(f"Total waypoints: {len(points)}")
                    print(f"First point: {points[0].strip()}")
                    print(f"Last point: {points[-1].strip()}")
                else:
                    print("ERROR: No geometry returned.")
            else:
                print(f"FAILED! Status code: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"Request failed with error: {str(e)}")

asyncio.run(run_test())
