from __future__ import annotations

import heapq
import uuid
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from app.models.vessel import Vessel
from app.schemas.route import RouteCreate, RouteRequest
from app.services.routing.grid import GridBuilder, Node
from app.services.routing.planner import RoutePlanner


def _parse_lonlat(value: str) -> Tuple[float, float]:
    parts = [float(x) for x in value.split(",")]
    if len(parts) != 2:
        raise ValueError(f"Expected 'lon,lat', got {value!r}")
    return parts[0], parts[1]


class DijkstraShortestPlanner(RoutePlanner):
    """Uniform-cost shortest-path planner (true geometric shortest path).

    The ``SHORTEST`` objective in route comparison runs through this planner so
    it produces a route that minimizes great-circle distance only, independent of
    fuel, time, and risk terms. This is intentionally distinct from
    ``AStarRoutePlanner`` which optimizes a weighted multi-objective cost.
    """

    def __init__(self, resolution: float = 0.5, max_iterations: int = 20000):
        self.grid_builder = GridBuilder(resolution=resolution)
        self.max_iterations = max_iterations

    async def plan_route(
        self,
        request: RouteRequest,
        vessel: Vessel,
        risk_grid: Optional[Dict] = None,
    ) -> RouteCreate:
        try:
            origin_lon, origin_lat = _parse_lonlat(request.origin)
            dest_lon, dest_lat = _parse_lonlat(request.destination)
        except (ValueError, IndexError) as exc:
            raise ValueError(f"Invalid origin/destination: {exc}")

        origin_node = Node(lat=origin_lat, lon=origin_lon)
        goal_node = Node(lat=dest_lat, lon=dest_lon)

        snapped_start = self.grid_builder.snap_to_water(origin_node, max_radius_degrees=2.0)
        snapped_goal = self.grid_builder.snap_to_water(goal_node, max_radius_degrees=2.0)
        
        if not snapped_start:
            raise ValueError("Origin port is on land and no navigable water found within 2.0° search radius.")
        if not snapped_goal:
            raise ValueError("Destination port is on land and no navigable water found within 2.0° search radius.")
            
        origin_node = snapped_start
        goal_node = snapped_goal

        counter = 0
        heap: List[Tuple[float, int, Node]] = [(0.0, counter, origin_node)]
        came_from: Dict[Node, Node] = {}
        cost_so_far: Dict[Node, float] = {origin_node: 0.0}

        iterations = 0
        found = False
        goal_key = goal_node
        while heap and iterations < self.max_iterations:
            iterations += 1
            current_cost, _, current = heapq.heappop(heap)
            if current_cost > cost_so_far.get(current, float("inf")):
                continue
            if (
                current == goal_key
                or current.distance_to(goal_key) < self.grid_builder.resolution
            ):
                found = True
                goal_key = current
                break
            for neighbor in self.grid_builder.get_neighbors(current):
                step_km = current.distance_to(neighbor)
                new_cost = current_cost + step_km
                if new_cost < cost_so_far.get(neighbor, float("inf")):
                    cost_so_far[neighbor] = new_cost
                    came_from[neighbor] = current
                    counter += 1
                    heapq.heappush(heap, (new_cost, counter, neighbor))

        if not found and goal_key not in came_from and goal_node not in came_from:
            raise ValueError("No feasible shortest route found within max_iterations.")

        # Reconstruct path. ``goal_key`` is the node we actually reached.
        path: List[Node] = [goal_key]
        current = goal_key
        while current in came_from:
            current = came_from[current]
            path.append(current)
        if path[-1] is not origin_node:
            path.append(origin_node)
        path.reverse()

        distance_nm = 0.0
        total_risk = 0.0
        
        from app.services.routing.cost import CostCalculator
        cost_calc = CostCalculator()
        
        for i in range(len(path) - 1):
            dist = path[i].distance_to(path[i + 1])
            distance_nm += dist
            
            cell_risk = cost_calc.get_risk_at(path[i + 1], risk_grid)
            total_risk += (cell_risk if cell_risk is not None else 0.0) * dist

        risk_exposure = total_risk
        risk_score = total_risk / distance_nm if distance_nm > 0 else 0.0

        if vessel.cruising_speed and vessel.cruising_speed > 0:
            hours = distance_nm / vessel.cruising_speed
        else:
            hours = 0.0
        eta = request.departure_time + timedelta(hours=hours)
        fuel = hours * vessel.fuel_consumption

        coords_str = ", ".join(f"{node.lon} {node.lat}" for node in path)
        wkt = f"LINESTRING({coords_str})"

        return RouteCreate(
            origin=request.origin,
            destination=request.destination,
            vessel_id=vessel.vessel_id,
            departure_time=request.departure_time,
            geometry=wkt,
            distance=distance_nm,
            travel_time=hours,
            eta=eta,
            estimated_fuel=fuel,
            risk_score=risk_score,
            risk_exposure=risk_exposure,
            objective_type=request.objective_type,
            algorithm_version="DijkstraShortest-v1.0",
            risk_data_status="available" if risk_grid else "not_applicable",
            ml_prediction_status="unavailable",
            warnings=["Dijkstra planner minimizes distance only. Environmental hazards were ignored during generation, but risk metrics are evaluated for comparison."],
            waypoints=None
        )
