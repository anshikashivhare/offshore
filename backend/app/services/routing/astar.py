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

    def _grid_for_voyage(self, start: Node, goal: Node) -> GridBuilder:
        """Use a coarser geographic search grid for ocean-spanning voyages.

        The base 0.5° grid remains appropriate around Antarctic ice and coast
        lines.  Searching the same grid across thousands of nautical miles
        creates far more nodes than the interactive request budget allows.
        This only changes the routing resolution; all nodes remain WGS84
        latitude/longitude and every edge is land-checked.
        """
        if self.grid_builder.resolution != 0.5:
            return self.grid_builder

        distance_nm = start.distance_to(goal)
        if distance_nm >= 4_000:
            return GridBuilder(resolution=2.0)
        if distance_nm >= 2_000:
            return GridBuilder(resolution=1.0)
        return self.grid_builder

    def _refine_final_approach(self, path: List[Node], goal: Node) -> List[Node]:
        """Replace a coarse final edge with a fine, water-only coastal approach.

        A global grid is useful in the open ocean, but its final diagonal can
        visually and physically clip a coastline.  This short A* pass uses the
        base (0.5°) grid for the final leg while retaining the same land-mask
        checks applied everywhere else.
        """
        if len(path) < 2 or self.grid_builder.resolution >= 1.0:
            return path

        approach_start = path[-2]
        if approach_start.distance_to(goal) > 240.0:
            return path

        queue = [(approach_start.distance_to(goal), 0, approach_start)]
        came_from: Dict[Node, Node] = {}
        cost: Dict[Node, float] = {approach_start: 0.0}
        counter = 0

        for _ in range(4_000):
            if not queue:
                break
            _, _, current = heapq.heappop(queue)
            if current == goal:
                refined = [current]
                while current in came_from:
                    current = came_from[current]
                    refined.append(current)
                refined.reverse()
                return path[:-2] + refined

            for neighbor in self.grid_builder.get_neighbors(current):
                candidate = cost[current] + current.distance_to(neighbor)
                if candidate >= cost.get(neighbor, float("inf")):
                    continue
                cost[neighbor] = candidate
                came_from[neighbor] = current
                counter += 1
                priority = candidate + neighbor.distance_to(goal)
                heapq.heappush(queue, (priority, counter, neighbor))

        # If no fine-water approach is available, keep the validated global
        # route rather than synthesizing a connector through land.
        return path

    async def plan_route(
        self, request: RouteRequest, vessel: Vessel, risk_grid: Any, demo_mode: bool = False
    ) -> RouteCreate:
        try:
            origin_coords = [float(x) for x in request.origin.split(",")]
            dest_coords = [float(x) for x in request.destination.split(",")]
        except ValueError:
            raise ValueError("Origin and destination must be 'lon,lat' format.")

        start_node = Node(lat=origin_coords[1], lon=origin_coords[0])
        goal_node = Node(lat=dest_coords[1], lon=dest_coords[0])
        grid_builder = self._grid_for_voyage(start_node, goal_node)
        
        # Keep port snapping at the fine base resolution.  A coarse ocean grid
        # is efficient for the voyage itself, but can round a coastal port
        # onto land and miss nearby water inside a two-degree search radius.
        snapped_start = self.grid_builder.snap_to_water(start_node, max_radius_degrees=2.0)
        snapped_goal = self.grid_builder.snap_to_water(goal_node, max_radius_degrees=2.0)
        
        if not snapped_start:
            raise ValueError("Origin port is on land and no navigable water found within 2.0° search radius.")
        if not snapped_goal:
            raise ValueError("Destination port is on land and no navigable water found within 2.0° search radius.")
            
        start_node = snapped_start
        goal_node = snapped_goal

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
        # A longer voyage uses fewer degrees per node on a coarser grid, but
        # still needs to search around continents.  The former fixed limit of
        # 1,500 nodes was only suitable for local Antarctic passages.
        max_iterations = 8_000 if grid_builder.resolution > self.grid_builder.resolution else 1_500
        
        missing_risk = any(v is None for k,v in risk_grid.items()) if isinstance(risk_grid, dict) and risk_grid else True

        # Precompute minimum possible cost per NM for admissible heuristic
        sog_max = vessel.cruising_speed if vessel.cruising_speed > 0 else 12.0
        min_cost_per_nm = (weights.alpha * (vessel.fuel_consumption / sog_max) + weights.beta * (1.0 / sog_max))
        # In demo mode there is no verified risk surface to optimize against.
        # Prefer a goal-directed search so a global exploratory voyage does
        # not exhaust the interactive budget by surveying an entire ocean.
        # Production keeps the near-admissible weight for risk-aware routing.
        heuristic_weight = 8.0 if demo_mode else 1.05

        closed_set = set()

        while open_set:
            iterations += 1
            if iterations > max_iterations:
                raise ValueError("No navigable water route found within the configured search limits.")

            _, _, current, current_time = heapq.heappop(open_set)
            
            if current in closed_set:
                continue
            closed_set.add(current)

            if (current == goal_node or current.distance_to(goal_node) < grid_builder.resolution * 60 * 1.5):
                return self._reconstruct_route(
                    came_from, current, start_node, goal_node, vessel, request, risk_grid, arrival_times, env_conditions_at, demo_mode, missing_risk
                )

            neighbors = grid_builder.get_neighbors(current)
            for neighbor in neighbors:
                if neighbor in closed_set:
                    continue
                if not self.constraint_checker.is_navigable(neighbor, vessel, risk_grid):
                    continue

                # Fetch 4D conditions at neighbor arrival time
                # Estimate a rough ETA just for the environmental lookup
                rough_dist = current.distance_to(neighbor)
                rough_speed = vessel.cruising_speed if vessel.cruising_speed > 0 else 12.0
                rough_eta = current_time + timedelta(hours=(rough_dist / rough_speed))
                
                env = global_forecast_grid.get_conditions(neighbor.lat, neighbor.lon, rough_eta)
                risk = self.cost_calculator.get_risk_at(neighbor, risk_grid)
                
                if risk is None:
                    if demo_mode:
                        # Demo fallback path: do not represent unknown risk as verified 0.0
                        # Assign an arbitrary unverified penalty instead
                        effective_risk = 0.5 
                    else:
                        if request.objective_type == ObjectiveType.SAFEST:
                            raise ValueError("Safety First objective requires verified risk data. Missing ML predictions.")
                        effective_risk = 0.0
                else:
                    effective_risk = risk

                edge_cost = scorer.calculate_edge_cost_4d(
                    current, neighbor, vessel, effective_risk, env
                )
                
                if edge_cost == float('inf'):
                    continue # Hard constraint failed

                tentative_g_score = g_score[current] + edge_cost

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    # Use min_cost_per_nm to scale the heuristic
                    f_score[neighbor] = tentative_g_score + self._heuristic(neighbor, goal_node) * min_cost_per_nm * heuristic_weight
                    
                    # Exact time propagation based on the exact effective speed
                    sog = scorer.get_effective_speed(current, neighbor, vessel, env)
                    if sog > 0:
                        exact_eta = current_time + timedelta(hours=(rough_dist / sog))
                        arrival_times[neighbor] = exact_eta
                        env_conditions_at[neighbor] = env

                        heapq.heappush(open_set, (f_score[neighbor], id(neighbor), neighbor, exact_eta))

        raise ValueError("No navigable water route found within the configured search limits.")

    def _reconstruct_route(
        self,
        came_from: Dict[Node, Node],
        current: Node,
        start_node: Node,
        goal_node: Node,
        vessel: Vessel,
        request: RouteRequest,
        risk_grid: Any,
        arrival_times: Dict[Node, datetime],
        env_conditions_at: Dict[Node, dict],
        demo_mode: bool,
        missing_risk: bool
    ) -> RouteCreate:
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        
        # Ensure the final point matches the exact destination coordinate
        if path[-1] != goal_node:
            path.append(goal_node)
            # Estimate arrival time for the final segment
            dist_to_goal = path[-2].distance_to(goal_node)
            sog = vessel.cruising_speed if vessel.cruising_speed > 0 else 12.0
            arrival_times[goal_node] = arrival_times[path[-2]] + timedelta(hours=dist_to_goal / sog)
            env_conditions_at[goal_node] = env_conditions_at.get(path[-2], {})

        refined_path = self._refine_final_approach(path, goal_node)
        if refined_path != path:
            anchor = path[-2]
            anchor_eta = arrival_times.get(anchor, request.departure_time)
            anchor_env = env_conditions_at.get(anchor, {})
            for index in range(1, len(refined_path)):
                previous, node = refined_path[index - 1], refined_path[index]
                if node in arrival_times and node not in path[-2:]:
                    continue
                anchor_eta += timedelta(
                    hours=previous.distance_to(node) /
                    (vessel.cruising_speed if vessel.cruising_speed > 0 else 12.0)
                )
                arrival_times[node] = anchor_eta
                env_conditions_at[node] = anchor_env
            path = refined_path
        
        # Ensure the first point matches the exact origin coordinate (already done implicitly if start_node was exact)
        
        # Calculate final metrics
        total_distance = 0.0
        total_risk = 0.0
        
        for i in range(len(path) - 1):
            dist = path[i].distance_to(path[i + 1])
            total_distance += dist
            cell_risk = self.cost_calculator.get_risk_at(path[i + 1], risk_grid)
            # Ensure we don't present missing risk as 0.0 in the final score if it's missing in demo mode
            if cell_risk is None and demo_mode:
                total_risk += 0.5 * dist
            else:
                total_risk += (cell_risk if cell_risk is not None else 0.0) * dist

        total_time_hours = (arrival_times[path[-1]] - request.departure_time).total_seconds() / 3600.0
        total_fuel = total_time_hours * vessel.fuel_consumption
        eta = arrival_times[path[-1]]
        
        risk_exposure = total_risk
        risk_score = total_risk / total_distance if total_distance > 0 else 0.0

         # Geometry construction
        from app.services.routing.modes import get_data_provenance
        from app.schemas.route import WaypointDetail
        
        # Build coordinates list representing the valid water nodes
        coords_list = [f"{n.lon} {n.lat}" for n in path]
            
        coords_str = ", ".join(coords_list)
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

        if missing_risk:
            if demo_mode:
                risk_status = "demo_unverified"
                ml_status = "unavailable"
                warnings = ["DEMO ROUTE — Risk data unavailable. This route has NOT been verified against real-time environmental hazards. Do not use for actual navigation."]
            else:
                risk_status = "unavailable"
                ml_status = "unavailable"
                warnings = ["Risk data is unavailable or incomplete. Assuming 0.0 risk for path math. DO NOT navigate blindly."]
        else:
            risk_status = "available"
            ml_status = "available"
            warnings = []

        return RouteCreate(
            origin=request.origin,
            destination=request.destination,
            vessel_id=request.vessel_id,
            departure_time=request.departure_time,
            geometry=geometry,
            distance=total_distance,
            travel_time=total_time_hours,
            eta=eta,
            estimated_fuel=total_fuel,
            risk_score=risk_score,
            risk_exposure=risk_exposure,
            objective_type=request.objective_type,
            algorithm_version="AStar-4D-TimeAware-v1.0",
            risk_data_status=risk_status,
            ml_prediction_status=ml_status,
            warnings=warnings,
            waypoints=waypoints_detail
        )
