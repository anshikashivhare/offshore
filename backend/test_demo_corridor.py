"""End-to-end test of the demo corridor via HTTP."""
import urllib.request
import json
import time

def test_compare(label, payload):
    t0 = time.time()
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/routes/compare",
        data=data_bytes,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    print(f"=== {label} ===")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read())
            elapsed = time.time() - t0
            print(f"  Status: 200 ({elapsed:.3f}s)")
            p = body["recommended_route"]["properties"]
            print(f"  objective_type: {p['objective_type']}")
            print(f"  risk_score: {p['risk_score']}")
            print(f"  risk_data_status: {p['risk_data_status']}")
            print(f"  ml_prediction_status: {p['ml_prediction_status']}")
            print(f"  land_avoidance_validated: {p['land_avoidance_validated']}")
            print(f"  distance: {p['distance']}")
            print(f"  travel_time: {p['travel_time']}")
            print(f"  waypoints: {len(p.get('waypoints') or [])}")
            print(f"  alternatives: {len(body.get('alternatives', []))}")
            for alt in body.get("alternatives", []):
                ap = alt["route"]["properties"]
                print(f"    alt: {ap['objective_type']} risk={ap['risk_score']} dist={ap['distance']}")
            coords = body["recommended_route"]["geometry"]["coordinates"]
            print(f"  First coord: {coords[0]}")
            print(f"  Last coord: {coords[-1]}")
            if body.get("explanation"):
                print(f"  explanation: {body['explanation'][:80]}...")
            return body
    except urllib.error.HTTPError as e:
        elapsed = time.time() - t0
        print(f"  HTTP Error: {e.code} ({elapsed:.3f}s)")
        print(f"  detail: {e.read().decode()[:300]}")
        return None
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  Error: {e} ({elapsed:.3f}s)")
        return None


# TEST A: Sydney -> Rothera, Safety First
test_compare("TEST A: Sydney -> Rothera (safest)", {
    "origin": "151.2,-33.87",
    "destination": "-68.13,-67.57",
    "vessel_id": "3a92b8d0-5e8a-4c28-8d4e-1b7f2c69d4a1",
    "departure_time": "2026-09-01T00:00:00Z",
    "objective_type": "safest",
})
print()

# TEST B: Rothera -> Sydney, Safety First
test_compare("TEST B: Rothera -> Sydney (safest)", {
    "origin": "-68.13,-67.57",
    "destination": "151.2,-33.87",
    "vessel_id": "3a92b8d0-5e8a-4c28-8d4e-1b7f2c69d4a1",
    "departure_time": "2026-09-01T00:00:00Z",
    "objective_type": "safest",
})
print()

# TEST C: Sydney -> Rothera, different priorities
test_compare("TEST C: Sydney -> Rothera (fastest)", {
    "origin": "151.2,-33.87",
    "destination": "-68.13,-67.57",
    "vessel_id": "3a92b8d0-5e8a-4c28-8d4e-1b7f2c69d4a1",
    "departure_time": "2026-09-01T00:00:00Z",
    "objective_type": "fastest",
})
print()

# TEST D: Non-demo route (should not intercept)
test_compare("TEST D: Cape Town -> Rothera (non-demo)", {
    "origin": "18.42,-33.92",
    "destination": "-68.13,-67.57",
    "vessel_id": "3a92b8d0-5e8a-4c28-8d4e-1b7f2c69d4a1",
    "departure_time": "2026-09-01T00:00:00Z",
    "objective_type": "safest",
})
print()

# TEST E: Demo scene endpoint
print("=== TEST E: Demo scene ===")
try:
    req = urllib.request.Request("http://localhost:8000/api/v1/routes/demo_scene")
    with urllib.request.urlopen(req, timeout=10) as resp:
        scene = json.loads(resp.read())
        print(f"  Keys: {list(scene.keys())}")
        print(f"  riskCells: {len(scene.get('riskCells', []))}")
        print(f"  icebergs: {len(scene.get('icebergs', []))}")
        print(f"  tracks: {len(scene.get('tracks', []))}")
        print(f"  trajectories: {len(scene.get('trajectories', []))}")
        print(f"  uncertainty: {len(scene.get('uncertainty', []))}")
except Exception as e:
    print(f"  Error: {e}")
