import heapq
from datetime import timedelta, datetime
from typing import Any, Dict, List, Optional

from app.models.enums import ObjectiveType
from app.models.vessel import Vessel
from app.schemas.route import OptimizationWeights, RouteCreate, RouteRequest
from app.services.routing.constraints import VesselConstraintChecker
from app.services.routing.cost import CostCalculator, RouteScorer
from app.services.routing.grid import GridBuilder, Node
from app.services.routing.planner import RoutePlanner


class AStarRoutePlanner(RoutePlanner):
    def __init__(self, resolution: float = 0.5):
        self.grid_builder = GridBuilder(resolution=resolution)
        self.cost_calculator = CostCalculator()
        self.constraint_checker = VesselConstraintChecker()

    def _get_weights_for_objective(
        self, objective: ObjectiveType, request_weights: Optional[OptimizationWeights]
    ) -> OptimizationWeights:
        if request_weights:
            return request_weights

        if objective == ObjectiveType.FASTEST:
            return OptimizationWeights(alpha=0.1, beta=0.8, gamma=0.1)
        elif objective == ObjectiveType.SAFEST:
            return OptimizationWeights(alpha=0.1, beta=0.1, gamma=0.8)
        elif objective == ObjectiveType.FUEL_EFFICIENT:
            return OptimizationWeights(alpha=0.8, beta=0.1, gamma=0.1)

        return OptimizationWeights()

    def _heuristic(self, a: Node, b: Node) -> float:
        """Straight-line distance heuristic"""
        return a.distance_to(b)

    async def plan_route(
        self, request: RouteRequest, vessel: Vessel, risk_grid: Any
    ) -> RouteCreate:
        try:
            origin_coords = [float(x) for x in request.origin.split(",")]
            dest_coords = [float(x) for x in request.destination.split(",")]
        except ValueError:
            raise ValueError("Origin and destination must be 'lon,lat' format.")

        start_node = Node(lat=origin_coords[1], lon=origin_coords[0])
        goal_node = Node(lat=dest_coords[1], lon=dest_coords[0])

        weights = self._get_weights_for_objective(
            request.objective_type, request.weights
        )
        scorer = RouteScorer(weights, self.cost_calculator)
        
        # Import global forecast grid inside method to avoid circular imports if any
        from app.services.environment.forecast_grid import global_forecast_grid
        from app.services.routing.modes import get_data_provenance

        # Prefetch grid over a bounding box - simplified to straight line sample here
        # Note: Pre-fetching must happen outside the A* loop!
        # For prototype, we prefetch a simplified corridor
        await global_forecast_grid.prefetch_corridor([start_node, goal_node])

        open_set = []
        # State: (f_score, id(node), node, current_eta)
        heapq.heappush(open_set, (0.0, id(start_node), start_node, request.departure_time))

        came_from = {}
        g_score: Dict[Node, float] = {start_node: 0.0}
        f_score: Dict[Node, float] = {
            start_node: self._heuristic(start_node, goal_node)
        }
        
        arrival_times: Dict[Node, datetime] = {start_node: request.departure_time}
        env_conditions_at: Dict[Node, dict] = {start_node: {}}

        iterations = 0
        max_iterations = 20000

        while open_set:
            iterations += 1
            if iterations > max_iterations:
                raise ValueError("No feasible route exists: exceeded maximum iterations.")

            _, _, current, current_time = heapq.heappop(open_set)

            if (current == goal_node or current.distance_to(goal_node) < self.grid_builder.resolution):
                return self._reconstruct_route(
                    came_from, current, start_node, vessel, request, risk_grid, arrival_times, env_conditions_at
                )

            neighbors = self.grid_builder.get_neighbors(current)
            for neighbor in neighbors:
                if not self.constraint_checker.is_navigable(neighbor, vessel, risk_grid):
                    continue

                # Fetch 4D conditions at neighbor arrival time
                # Estimate a rough ETA just for the environmental lookup
                rough_dist = current.distance_to(neighbor)
                rough_speed = vessel.cruising_speed if vessel.cruising_speed > 0 else 12.0
                rough_eta = current_time + timedelta(hours=(rough_dist / rough_speed))
                
                env = global_forecast_grid.get_conditions(neighbor.lat, neighbor.lon, rough_eta)
                risk = self.cost_calculator.get_risk_at(neighbor, risk_grid)
                
                edge_cost = scorer.calculate_edge_cost_4d(
                    current, neighbor, vessel, risk, env
                )
                
                if edge_cost == float('inf'):
                    continue # Hard constraint failed

                tentative_g_score = g_score[current] + edge_cost

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self._heuristic(neighbor, goal_node) * weights.beta
                    
                    # Exact time propagation based on the exact effective speed
                    sog = scorer.get_effective_speed(current, neighbor, vessel, env)
                    if sog > 0:
                        exact_eta = current_time + timedelta(hours=(rough_dist / sog))
                        arrival_times[neighbor] = exact_eta
                        env_conditions_at[neighbor] = env

                        heapq.heappush(open_set, (f_score[neighbor], id(neighbor), neighbor, exact_eta))

        raise ValueError("No feasible route exists between origin and destination under current constraints.")

    def _reconstruct_route(
        self,
        came_from: Dict[Node, Node],
        current: Node,
        start_node: Node,
        vessel: Vessel,
        request: RouteRequest,
        risk_grid: Any,
        arrival_times: Dict[Node, datetime],
        env_conditions_at: Dict[Node, dict]
    ) -> RouteCreate:
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        
        # Calculate final metrics
        total_distance = 0.0
        total_risk = 0.0
        
        for i in range(len(path) - 1):
            dist = path[i].distance_to(path[i + 1])
            total_distance += dist
            total_risk += self.cost_calculator.get_risk_at(path[i + 1], risk_grid) * dist

        total_time_hours = (arrival_times[path[-1]] - request.departure_time).total_seconds() / 3600.0
        total_fuel = total_time_hours * vessel.fuel_consumption
        eta = arrival_times[path[-1]]
         # Geometry construction
        from app.services.routing.modes import get_data_provenance
        from app.schemas.route import WaypointDetail
        
        coords_str = ", ".join([f"{n.lon} {n.lat}" for n in path])
        geometry = f"LINESTRING({coords_str})"
        
        waypoints_detail = []
        for n in path:
            w_eta = arrival_times.get(n, request.departure_time)
            hours_from_start = (w_eta - request.departure_time).total_seconds() / 3600.0
            prov = get_data_provenance(hours_from_start, 14)
            env = env_conditions_at.get(n, {})
            waypoints_detail.append(
                WaypointDetail(
                    lat=n.lat,
                    lon=n.lon,
                    eta=w_eta,
                    data_provenance=prov,
                    env_conditions=env
                )
            )

        return RouteCreate(
            origin=request.origin,
            destination=request.destination,
            vessel_id=request.vessel_id,
            departure_time=request.departure_time,
            geometry=geometry,
            distance=total_distance,
            eta=eta,
            estimated_fuel=total_fuel,
            risk_score=total_risk,
            objective_type=request.objective_type,
            algorithm_version="AStar-4D-TimeAware-v1.0",
            waypoints=waypoints_detail
        )
