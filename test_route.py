import urllib.request
import json
import datetime

url = "http://127.0.0.1:8000/api/v1/routes/plan"
payload = {
    "vessel_id": "3a92b8d0-5e8a-4c28-8d4e-1b7f2c69d4a1",
    "origin": "-60,-65",
    "destination": "-55,-60",
    "departure_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "objective_type": "fastest",
    "custom_vessel_config": None
}
data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        with open("route_response.json", "w") as f:
            json.dump(result, f, indent=2)
        print("Response saved to route_response.json")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code}")
    print(e.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
