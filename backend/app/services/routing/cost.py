from typing import Any

from app.models.vessel import Vessel
from app.schemas.route import OptimizationWeights
from app.services.routing.grid import Node


class FuelEstimator:
    def estimate_fuel(self, vessel: Vessel, distance_nm: float) -> float:
        """
        Estimate fuel consumption over a given distance.
        Simplified: consumption is rate * time. Time = distance / speed.
        """
        if vessel.cruising_speed <= 0:
            return float("inf")
        hours = distance_nm / vessel.cruising_speed
        return hours * vessel.fuel_consumption


class TravelTimeEstimator:
    def estimate_time(self, vessel: Vessel, distance_nm: float) -> float:
        """Estimate travel time in hours."""
        if vessel.cruising_speed <= 0:
            return float("inf")
        return distance_nm / vessel.cruising_speed


class CostCalculator:
    def __init__(self):
        self.fuel_estimator = FuelEstimator()
        self.time_estimator = TravelTimeEstimator()

    def get_risk_at(self, node: Node, risk_grid: Any) -> float:
        """
        Extract the composite risk value from the risk grid for a given coordinate.
        Mock implementation:
        We will look up risk_grid dict if available, else default to 0.0
        """
        if isinstance(risk_grid, dict):
            # risk_grid could be a dict of (lat, lon) rounded to 1 dec -> risk
            key = (round(node.lat, 1), round(node.lon, 1))
            risk_entry = risk_grid.get(key, 0.0)
            if isinstance(risk_entry, dict):
                return max(risk_entry.values()) if risk_entry else 0.0
            return float(risk_entry)
        return 0.0


class RouteScorer:
    def __init__(self, weights: OptimizationWeights, cost_calc: CostCalculator):
        self.weights = weights
        self.cost_calc = cost_calc

    def calculate_edge_cost(
        self, current: Node, neighbor: Node, vessel: Vessel, risk_grid: Any
    ) -> float:
        """Calculate combined edge cost using optimization weights."""
        distance = current.distance_to(neighbor)

        fuel = self.cost_calc.fuel_estimator.estimate_fuel(vessel, distance)
        time = self.cost_calc.time_estimator.estimate_time(vessel, distance)
        risk = self.cost_calc.get_risk_at(neighbor, risk_grid)

        # We normalize components so they are somewhat comparable, or simply weight them.
        # This is a basic cost function representation.
        cost = (
            self.weights.alpha * fuel
            + self.weights.beta * time
            + self.weights.gamma
            * (risk * distance)  # Risk is accumulated over distance
        )
        return cost
