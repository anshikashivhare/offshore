import asyncio
import httpx
import time

async def run_test():
    url = 'http://localhost:8000/api/v1/routes/plan'
    payload = {
        'vessel_id': '3a92b8d0-5e8a-4c28-8d4e-1b7f2c69d4a1',
        'origin': '-44.72,-60.75',
        'destination': '110.53,-66.28',
        'departure_time': '2026-09-19T06:00:00Z',
        'objective_type': 'safest'
    }

    start_time = time.time()
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload)
            print(f'Status: {response.status_code}')
            print(f'Time: {time.time() - start_time:.2f}s')
            
            if response.status_code == 201:
                data = response.json()
                print(f'Success. Dist: {data["properties"]["distance"]} NM')
            else:
                print(response.text[:200])
        except Exception as e:
            print(f'Error: {e}')

asyncio.run(run_test())
