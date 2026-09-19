import asyncio
import httpx
import time
import json

async def run_test():
    url = "http://localhost:8000/api/v1/routes/plan"
    
    # Rothera to Sydney
    payload = {
        "vessel_id": "848e0cd9-bde8-48b8-b4b9-8e4af900bbfb",
        "origin": "-68.13,-67.57", # Rothera (lon, lat)
        "destination": "151.2,-33.8", # Sydney (lon, lat)
        "departure_time": "2026-09-19T06:00:00Z",
        "objective_type": "fastest"
    }

    print("Testing route from Rothera (-68.13, -67.57) to Sydney (151.2, -33.8)...")
    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            response = await client.post(url, json=payload)
            end_time = time.time()
            
            if response.status_code == 201:
                data = response.json()
                print(f"SUCCESS! Status: {response.status_code}")
                print(f"Time taken: {end_time - start_time:.2f} seconds")
                geometry = data.get('geometry', '')
                if geometry:
                    points = geometry.replace("LINESTRING(", "").replace(")", "").split(",")
                    print(f"Total waypoints: {len(points)}")
                else:
                    print("ERROR: No geometry")
            else:
                print(f"FAILED! Status code: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"Request failed with error: {str(e)}")

asyncio.run(run_test())
