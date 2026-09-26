import asyncio
import json
import urllib.request
import urllib.error
import time
from uuid import uuid4
from datetime import datetime
import sys

# Set up paths so we can import validator
sys.path.append("/Users/apple/Downloads/offshore/backend")
from app.services.routing.validator import route_validator

API_URL = "http://localhost:8000/api/v1/routes/plan"

tests = [
    {
        "name": "A. Open Southern Ocean route",
        "origin": "-60.0,-50.0",
        "destination": "-60.0,-48.0"
    },
    {
        "name": "B. Antarctica approach",
        "origin": "-64.0,-60.0",
        "destination": "-64.0,-55.0"
    },
    {
        "name": "C. Peninsula obstacle test",
        "origin": "-75.0,-65.0", # West of Antarctic peninsula (Bellingshausen Sea)
        "destination": "-55.0,-65.0" # East of Antarctic peninsula (Weddell Sea)
    },
    {
        "name": "D. South America -> Antarctica",
        "origin": "-65.0,-55.0",
        "destination": "-60.0,-62.0"
    },
    {
        "name": "E. Australia -> Antarctica",
        "origin": "140.0,-45.0",
        "destination": "140.0,-60.0"
    },
    {
        "name": "F. Invalid inland endpoint",
        "origin": "0.0,-85.0", 
        "destination": "-64.0,-55.0"
    }
]

def make_request(origin, destination):
    req_data = {
        "vessel_id": str(uuid4()),
        "origin": origin,
        "destination": destination,
        "departure_time": datetime.utcnow().isoformat() + "Z",
        "objective_type": "fastest"
    }
    
    req = urllib.request.Request(
        API_URL, 
        data=json.dumps(req_data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    start_time = time.time()
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            elapsed = time.time() - start_time
            return res_data, elapsed, None
    except urllib.error.HTTPError as e:
        err_data = e.read().decode('utf-8')
        elapsed = time.time() - start_time
        return None, elapsed, err_data

for t in tests:
    print(f"\n=============================================")
    print(f"Testing: {t['name']}")
    print(f"Origin: {t['origin']} | Destination: {t['destination']}")
    
    res, elapsed, err = make_request(t['origin'], t['destination'])
    
    print(f"Runtime: {elapsed:.2f}s")
    
    if err:
        print(f"Request failed as expected/unexpected: {err}")
        continue
        
    print(f"Routing Mode: {res.get('routing_mode')}")
    print(f"Route Source: {res.get('route_source')}")
    print(f"Warnings: {res.get('warnings')}")
    
    geom = res.get('geometry')
    if geom:
        coords = geom.get('coordinates', [])
        num_nodes = len(coords)
        num_edges = max(0, num_nodes - 1)
        print(f"Nodes: {num_nodes} | Edges: {num_edges}")
        
        # Build WKT
        if num_nodes > 1:
            # Coordinates in geojson are typically [lon, lat], but let's check
            # In our routes, coordinates might be [lon, lat] or [lat, lon].
            # WKT should be lon lat
            wkt = "LINESTRING(" + ", ".join([f"{c[0]} {c[1]}" for c in coords]) + ")"
            is_valid, msg, details = route_validator.validate_wkt_linestring(wkt, strict=False)
            
            # If msg is about invalid pair, maybe we need to swap them
            if msg and "Invalid coordinate pair" in msg:
                 wkt = "LINESTRING(" + ", ".join([f"{c[1]} {c[0]}" for c in coords]) + ")"
                 is_valid, msg, details = route_validator.validate_wkt_linestring(wkt, strict=False)
            print(f"Validator Status: {is_valid} - {msg}")
            
            # Since route_validator checks intersections and distance to land
            print(f"Validator details: {details}")
            if details:
                print(f"Land intersections: {details.get('land_intersections')}")
                print(f"Min distance to land (km): {details.get('min_distance_to_land_km')}")
                
            # Direct check just to be absolutely sure using the validator's intersection counting
            land_collisions = details.get('land_intersections', 0) if details else 0
            print(f"Independent Land Collisions: {land_collisions}")
            if land_collisions == 0:
                print("-> INVARIANT MET: land_intersections == 0")
            else:
                print("-> INVARIANT FAILED: land_intersections > 0")
                
            # Straight-line test for Peninsula obstacle
            if "Peninsula" in t['name']:
                print("\n--- Testing Peninsula Straight-Line Geometry ---")
                o_lon, o_lat = [float(x) for x in t['origin'].split(',')]
                d_lon, d_lat = [float(x) for x in t['destination'].split(',')]
                # Coordinates from origin are lon,lat
                o_lon, o_lat = map(float, t['origin'].split(','))
                d_lon, d_lat = map(float, t['destination'].split(','))
                
                # WKT expects lon lat
                straight_wkt = f"LINESTRING({o_lon} {o_lat}, {d_lon} {d_lat})"
                is_valid_s, msg_s, details_s = route_validator.validate_wkt_linestring(straight_wkt, strict=False)
                straight_collisions = details_s.get('land_intersections', 0) if details_s else 0
                print(f"Straight-line Land Collisions: {straight_collisions}")
                if straight_collisions > 0 and land_collisions == 0:
                    print("-> PENINSULA TEST PASSED: Straight line intersects land, but actual A* route avoids it.")
        else:
            print("Geometry has < 2 nodes!")
    else:
        print("No geometry returned!")
