import asyncio
import httpx
from datetime import datetime, timezone

async def main():
    async with httpx.AsyncClient() as client:
        req = {
            "vessel_id": "8d56cc55-5f45-58ad-b758-6d68f1c48ec3",
            "origin": "-64.0, -69.0",
            "destination": "-60.0, -67.5",
            "departure_time": "2026-09-18T06:00:00Z",
            "objective_type": "safest"
        }
        res = await client.post("http://localhost:8000/api/v1/routes/plan", json=req, timeout=30.0)
        print("Status:", res.status_code)
        print("Error:", res.text)

asyncio.run(main())
