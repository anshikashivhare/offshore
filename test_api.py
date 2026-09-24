import urllib.request
import json

def test_api():
    # Get vessels
    req = urllib.request.Request('http://localhost:8000/api/v1/vessels')
    with urllib.request.urlopen(req) as resp:
        vessels = json.loads(resp.read().decode())
        vessel_id = vessels["data"][0]["vessel_id"]

    payload = {
        'origin': '-69.21,-52.60',
        'destination': '-3.79,-71.98',
        'vessel_id': vessel_id,
        'departure_time': '2026-09-13T12:00:00Z',
        'objective_type': 'safest',
        'weights': {'alpha': 0.33, 'beta': 0.33, 'gamma': 0.34}
    }
    
    req = urllib.request.Request(
        'http://localhost:8000/api/v1/routes/compare',
        data=json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            print("SUCCESS")
    except urllib.error.HTTPError as e:
        print(f"ERROR: {e.code}")
        print(e.read().decode())

test_api()
