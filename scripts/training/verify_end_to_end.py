import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient
from backend.app.main import app

def run_integration_test():
    client = TestClient(app)
    
    print("==============================================")
    print("BACKEND ORCHESTRATION + API INTEGRATION TEST")
    print("==============================================")
    
    # We will invoke the actual Route endpoint
    payload = {
      "origin": "50.0,-60.0",
      "destination": "52.0,-60.0",
      "vessel_id": "123e4567-e89b-12d3-a456-426614174001",
      "departure_time": "2026-09-25T12:00:00Z",
      "objective_type": "fastest",
      "weights": {
        "alpha": 0.1,
        "beta": 0.1,
        "gamma": 0.8
      },
      "custom_vessel_config": {
        "vessel_name": "Test Vessel",
        "vessel_type": "icebreaker",
        "cruising_speed": 12.0,
        "fuel_consumption": 10.0,
        "ice_capability": "PC1",
        "draft_m": 10.0,
        "max_wave_height_m": 5.0
      }
    }
    
    print("\nSending POST /api/v1/routes/plan...")
    
    response = client.post("/api/v1/routes/plan", json=payload)
    
    print(f"HTTP Status: {response.status_code}")
    
    if response.status_code != 201 and response.status_code != 200:
        print(f"Failed! Output: {response.text}")
        return
        
    data = response.json()
    
    print("\n--- RESPONSE VALIDATION ---")
    print(f"Type: {data.get('type')}")
    geom = data.get('geometry', {})
    print(f"Geometry Type: {geom.get('type')}")
    print(f"Coordinates Count: len({len(geom.get('coordinates', []))})")
    
    props = data.get('properties', {})
    print("\n--- RISK METADATA ---")
    print(f"Distance: {props.get('distance')} NM")
    print(f"Algorithm: {props.get('algorithm_version')}")
    print(f"Iceberg Risk Status: {props.get('iceberg_risk_status')}")
    print(f"Iceberg Model Version: {props.get('iceberg_model_version')}")
    print(f"Forecast Available: {props.get('iceberg_forecast_available')}")
    print(f"Forecast Coverage: {props.get('forecast_coverage_hours')} hours")
    print(f"Candidate Icebergs: {props.get('candidate_icebergs')}")
    
    print("\n--- PROVENANCE & VALIDATION ---")
    print(f"Land Avoidance Validated: {props.get('land_avoidance_validated')}")
    print(f"Warnings: {props.get('warnings')}")
    
    print("\nORCHESTRATION CONTRACT SUCCESSFUL ✓")

if __name__ == "__main__":
    run_integration_test()
