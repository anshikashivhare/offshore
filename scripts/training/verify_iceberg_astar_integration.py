import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.services.routing.grid import Node
from backend.app.services.risk.iceberg_risk import IcebergRiskEngine
from datetime import datetime, timedelta

def test_astar_causal():
    print("--- CAUSAL A* INTEGRATION TEST ---")
    engine = IcebergRiskEngine()
    
    # Antimeridian tests
    from backend.app.services.risk.iceberg_risk import wrapped_lon_diff
    print("Antimeridian:")
    print(f"179.9 -> -179.9 = {wrapped_lon_diff(-179.9, 179.9):.2f} (Expected: 0.20)")
    print(f"-179.9 -> 179.9 = {wrapped_lon_diff(179.9, -179.9):.2f} (Expected: -0.20)")
    print(f"179.0 -> -179.0 = {wrapped_lon_diff(-179.0, 179.0):.2f} (Expected: 2.00)")
    
    start_node = Node(lat=-60.0, lon=50.0)
    end_node = Node(lat=-60.0, lon=51.0)
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=3)
    
    # Fake Iceberg that crosses path
    ice_state = {"lat": -60.05, "lon": 50.55} # Will predict slightly NE
    pred = engine.predict_iceberg_trajectory(ice_state, start_time, [3])
    print(f"LSTM Prediction: {pred['predicted_latitude']:.4f}, {pred['predicted_longitude']:.4f}")
    
    # Evaluate edge risk
    risk_res = engine.evaluate_edge_risk(start_node, end_node, start_time, end_time, [pred])
    
    print("\n--- A* EDGE COST SIMULATION ---")
    # Base cost is distance
    distance = 1.0 # fake degrees
    cost_base = distance * 1.0
    
    if risk_res['navigable'] == False:
        cost_with_risk = float('inf')
        print("RESULT: EDGE REJECTED (HARD CONSTRAINT)")
    else:
        risk_penalty = risk_res['risk_index'] * distance * 100 # Heavy weight
        cost_with_risk = cost_base + risk_penalty
        print(f"Base Cost: {cost_base:.2f}")
        print(f"Iceberg Risk Index: {risk_res['risk_index']:.4f}")
        print(f"Cost with Risk Penalty: {cost_with_risk:.2f}")
    
    if cost_with_risk > cost_base:
        print("\nCAUSAL PROOF SUCCESS: ML output -> Iceberg predicted position -> CPA -> Non-zero risk -> Changed A* edge cost!")
    else:
        print("\nFAILED: Edge cost did not change.")

if __name__ == "__main__":
    test_astar_causal()
