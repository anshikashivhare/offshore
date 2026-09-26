import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

async def test_vessels():
    async with httpx.AsyncClient() as client:
        # We know from DB there are vessels. Let's list or just use a dummy one if list endpoint doesn't exist.
        pass

async def main():
    print("Testing backend endpoints...")
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Check health or similar if it exists
        # Actually, let's just test a direct route calculation
        for obj in ["fastest", "fuel_efficient", "safest"]:
            print(f"\n--- Testing objective: {obj} ---")
            payload = {
                "origin": "-65.0,-75.0",
                "destination": "-65.0,-70.0",
                "vessel_id": "8d56cc55-5f45-58ad-b758-6d68f1c48ec3",
                "departure_time": "2026-09-26T12:00:00Z",
                "objective_type": obj
            }
            try:
                resp = await client.post(f"{BASE_URL}/api/v1/routes/plan", json=payload)
                print(f"Status: {resp.status_code}")
                print(resp.text[:500])
            except Exception as e:
                print("Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
