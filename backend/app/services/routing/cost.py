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
        Returns None if risk data is unavailable for this coordinate.
        """
        if isinstance(risk_grid, dict) and risk_grid:
            key = (round(node.lat, 1), round(node.lon, 1))
            if key not in risk_grid:
                return None
            risk_entry = risk_grid.get(key)
            if isinstance(risk_entry, dict):
                return max(risk_entry.values()) if risk_entry else 0.0
            return float(risk_entry)
        return None


import math

class RouteScorer:
    def __init__(self, weights: OptimizationWeights, cost_calc: CostCalculator):
        self.weights = weights
        self.cost_calc = cost_calc

    def get_effective_speed(self, current: Node, neighbor: Node, vessel: Vessel, env_conditions: dict) -> float:
        """
        Calculates Speed Over Ground (SOG) from Speed Through Water (STW)
        using vector mathematics and heuristic penalties.
        """
        stw = getattr(vessel, "cruising_speed", 12.0)
        if stw <= 0:
            return 0.0
        
        # 2. Ocean Current Vector (simplified)
        c_vel = env_conditions.get("ocean_current_velocity") or 0.0
        c_dir = env_conditions.get("ocean_current_direction") or 0.0
        
        # 1. Heading vector
        dy = neighbor.lat - current.lat
        dx = neighbor.lon - current.lon
        heading_rad = math.atan2(dx, dy) # 0 is North, pi/2 is East
        heading_deg = (math.degrees(heading_rad) + 360) % 360
        
        current_angle_diff = math.radians(c_dir - heading_deg)
        c_parallel = c_vel * math.cos(current_angle_diff)
        
        # 3. Wind/Wave Heuristic Penalty
        w_vel = env_conditions.get("wind_speed_10m") or 0.0
        w_dir = env_conditions.get("wind_direction_10m") or 0.0
        wave_h = env_conditions.get("wave_height") or 0.0
        
        # Assuming wind 'from' direction
        wind_angle_diff = math.radians(w_dir - heading_deg)
        
        # Heuristic: headwind/headwaves slow down, tailwind has minimal effect
        # Penalty is proportional to wave height and headwind component
        headwind_comp = w_vel * math.cos(wind_angle_diff)
        
        penalty = 0.0
        if headwind_comp < 0: # Headwind
            penalty += abs(headwind_comp) * 0.05
        if wave_h > 1.0:
            penalty += wave_h * 0.5
            
        sog = stw + c_parallel - penalty
        return max(sog, 0.0)

    def calculate_edge_cost_4d(
        self, current: Node, neighbor: Node, vessel: Vessel, risk_score: float, env_conditions: dict
    ) -> float:
        """Calculate combined edge cost using 4D parameters."""
        
        # Hard Constraints
        max_wave = 5.0 # config later
        max_wind = 40.0 # config later
        
        wave_height = env_conditions.get("wave_height")
        if wave_height is None:
            wave_height = 0.0
            
        wind_speed = env_conditions.get("wind_speed_10m")
        if wind_speed is None:
            wind_speed = 0.0

        if wave_height > max_wave:
            return float("inf")
        if wind_speed > max_wind:
            return float("inf")
            
        distance = current.distance_to(neighbor)
        sog = self.get_effective_speed(current, neighbor, vessel, env_conditions)
        
        if sog <= 0:
            return float('inf')
            
        time_hours = distance / sog
        fuel = time_hours * vessel.fuel_consumption

        cost = (
            self.weights.alpha * fuel
            + self.weights.beta * time_hours
            + self.weights.gamma * (risk_score * distance)
        )
        return cost
