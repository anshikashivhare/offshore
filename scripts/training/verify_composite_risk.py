import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.services.routing.cost import RouteScorer, CostCalculator
from backend.app.schemas.route import OptimizationWeights
from backend.app.models.vessel import Vessel
from backend.app.services.routing.grid import Node

def run_analytical_aggregation_test():
    print("--- COMPOSITE AGGREGATION ANALYSIS ---")
    sea_ice_examples = [0.2, 0.8, 0.6]
    iceberg_examples = [0.8, 0.2, 0.6]
    
    print(f"{'Sea Ice':<10} | {'Iceberg':<10} | {'MAX (Current)':<15} | {'WEIGHTED (0.5)':<15} | {'PROBABILISTIC UNION'}")
    for si, ic in zip(sea_ice_examples, iceberg_examples):
        c_max = max(si, ic)
        c_weight = 0.5 * si + 0.5 * ic
        c_prob = 1 - (1 - si) * (1 - ic)
        print(f"{si:<10.2f} | {ic:<10.2f} | {c_max:<15.2f} | {c_weight:<15.2f} | {c_prob:.2f}")
        
def run_two_hazard_interaction():
    print("\n--- TWO HAZARD INTERACTION TEST (COST) ---")
    weights = OptimizationWeights(alpha=0.1, beta=0.8, gamma=0.1)
    scorer = RouteScorer(weights, CostCalculator())
    vessel = Vessel(cruising_speed=12.0, fuel_consumption=10.0)
    
    current = Node(lat=-60.0, lon=50.0)
    neighbor = Node(lat=-60.0, lon=51.0)
    dist = current.distance_to(neighbor)
    
    cases = [
        ("CASE A: Low Sea Ice, Low Iceberg", 0.1, 0.1),
        ("CASE B: High Sea Ice, Low Iceberg", 0.9, 0.1),
        ("CASE C: Low Sea Ice, High Iceberg", 0.1, 0.9),
        ("CASE D: High Sea Ice, High Iceberg", 0.9, 0.9)
    ]
    
    for name, si, ic in cases:
        # A* evaluates effective_risk as max(existing, iceberg)
        effective_risk = max(si, ic)
        cost = scorer.calculate_edge_cost_4d(current, neighbor, vessel, effective_risk, {})
        print(f"{name:<35} -> Max Risk: {effective_risk:.2f}, Final Edge Cost: {cost:.2f}")

if __name__ == "__main__":
    run_analytical_aggregation_test()
    run_two_hazard_interaction()
