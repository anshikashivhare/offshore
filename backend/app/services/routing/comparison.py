from __future__ import annotations

import copy
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.enums import ObjectiveType
from app.models.vessel import Vessel
from app.schemas.route import (OptimizationWeights, RouteAlternative,
                               RouteComparisonMetrics, RouteComparisonResponse,
                               RouteCreate, RouteProperties, RouteRequest,
                               RouteResponse)
from app.services.routing.planner import RoutePlanner
from app.utils.geojson import parse_wkt_linestring


def _avg(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


class RouteComparisonService:
    """Generate alternative routes for multiple objectives and rank them."""

    def __init__(
        self,
        planner: RoutePlanner,
        shortest_planner: Optional[RoutePlanner] = None,
    ):
        self.planner = planner
        self.shortest_planner = shortest_planner

    def _generate_explanation(
        self,
        recommended: RouteProperties,
        shortest: RouteProperties,
        objective: ObjectiveType,
    ) -> str:
        dist_diff = recommended.distance - shortest.distance
        
        # Use travel_time if available, else fallback to eta diff
        if recommended.travel_time is not None and shortest.travel_time is not None:
            time_diff = recommended.travel_time - shortest.travel_time
        else:
            time_diff = (recommended.eta - shortest.eta).total_seconds() / 3600.0
            
        fuel_diff = recommended.estimated_fuel - shortest.estimated_fuel
        
        # Use risk_exposure if available, else fallback to risk_score
        if recommended.risk_exposure is not None and shortest.risk_exposure is not None:
            risk_diff = recommended.risk_exposure - shortest.risk_exposure
        else:
            risk_diff = recommended.risk_score - shortest.risk_score

        parts = [
            f"This route was recommended because the objective is {objective.value.upper()}."
        ]
        if risk_diff < -0.01:
            parts.append(
                f"It significantly reduces risk exposure compared to the shortest path (by {-risk_diff:.2f})."
            )
        elif risk_diff > 0.01:
            parts.append(
                f"It accepts higher risk (by {risk_diff:.2f}) to achieve other goals."
            )
        else:
            parts.append("It maintains a similar risk profile to the baseline.")

        if time_diff > 0.1:
            parts.append(f"Estimated travel time increases by {time_diff:.1f} hours.")
        elif time_diff < -0.1:
            parts.append(f"It saves {abs(time_diff):.1f} hours of travel time.")
        else:
            parts.append("Negligible impact on travel time.")

        if fuel_diff < -1.0:
            parts.append(f"It also saves {abs(fuel_diff):.1f} units of fuel.")
        elif fuel_diff > 1.0:
            parts.append(f"This requires {fuel_diff:.1f} additional units of fuel.")

        return " ".join(parts)

    def _extract_uncertainty(self, risk_grid: Any) -> str:
        grid = risk_grid.cells if hasattr(risk_grid, 'cells') else risk_grid
        if not grid:
            return "Risk surface unavailable. Recommendation based on geometric distance only."
        confidences: List[float] = []
        for v in grid.values():
            if isinstance(v, dict):
                conf = v.get("confidence") or v.get("confidence_score")
                if isinstance(conf, (int, float)):
                    confidences.append(float(conf))
            elif isinstance(v, (int, float)):
                confidences.append(min(1.0, max(0.0, 1.0 - float(v))))
        if not confidences:
            return "Confidence unknown for the available risk surface."
        avg = _avg(confidences)
        if avg >= 0.75:
            return (
                f"High confidence (avg={avg:.2f}). Risk-aware pathfinding is reliable."
            )
        if avg >= 0.5:
            return (
                f"Medium confidence (avg={avg:.2f}). Forecasts have moderate variance."
            )
        return f"Low confidence (avg={avg:.2f}). Treat risk values as indicative only."

    def _get_warnings(self, risk_grid: Any) -> List[str]:
        warnings: List[str] = []
        grid = risk_grid.cells if hasattr(risk_grid, 'cells') else risk_grid
        if not grid:
            warnings.append(
                "Risk surface empty; route based on geometric shortest path."
            )
            return warnings
        high = 0
        for v in grid.values():
            if isinstance(v, (int, float)) and v >= 0.7:
                high += 1
            elif isinstance(v, dict):
                comp = v.get("composite") or v.get("composite_risk") or 0.0
                if isinstance(comp, (int, float)) and comp >= 0.7:
                    high += 1
        if high:
            warnings.append(
                f"{high} high-risk cells detected in the operational area; review route."
            )
        return warnings

    def _convert_to_response(self, route_create: RouteCreate) -> RouteResponse:
        props = RouteProperties(
            route_id=uuid.uuid4(),
            vessel_id=route_create.vessel_id,
            origin=route_create.origin,
            destination=route_create.destination,
            departure_time=route_create.departure_time,
            distance=route_create.distance,
            travel_time=route_create.travel_time,
            eta=route_create.eta,
            estimated_fuel=route_create.estimated_fuel,
            risk_score=route_create.risk_score,
            risk_exposure=route_create.risk_exposure,
            objective_type=route_create.objective_type,
            algorithm_version=route_create.algorithm_version,
            waypoints=route_create.waypoints,
            risk_data_status=route_create.risk_data_status,
            ml_prediction_status=route_create.ml_prediction_status,
            warnings=route_create.warnings,
        )
        try:
            geometry = parse_wkt_linestring(route_create.geometry)
        except Exception:
            geometry = {"type": "LineString", "coordinates": []}
        return RouteResponse(type="Feature", geometry=geometry, properties=props)

    async def compare_routes(
        self,
        base_request: RouteRequest,
        vessel: Vessel,
        risk_grid: Any,
    ) -> RouteComparisonResponse:
        import asyncio
        objectives = [
            ObjectiveType.SHORTEST,
            ObjectiveType.FASTEST,
            ObjectiveType.SAFEST,
            ObjectiveType.FUEL_EFFICIENT,
        ]
        if base_request.objective_type not in objectives:
            objectives.append(base_request.objective_type)

        routes_generated: Dict[ObjectiveType, RouteResponse] = {}
        errors: List[str] = []

        async def _plan_objective(obj: ObjectiveType):
            req = copy.deepcopy(base_request)
            req.objective_type = obj
            
            if obj != base_request.objective_type:
                req.weights = None
                
            if obj == ObjectiveType.SHORTEST and self.shortest_planner is not None:
                planner = self.shortest_planner
            elif obj == ObjectiveType.SHORTEST:
                # No dedicated shortest planner; force distance-only weights
                req.weights = OptimizationWeights(alpha=0.0, beta=1.0, gamma=0.0)
                planner = self.planner
            else:
                planner = self.planner

            try:
                route_create = await planner.plan_route(req, vessel, risk_grid)
                return obj, self._convert_to_response(route_create), None
            except ValueError as e:
                return obj, None, str(e)
            except Exception as e:
                return obj, None, f"Internal error: {str(e)}"

        results = await asyncio.gather(*[_plan_objective(obj) for obj in objectives])

        for obj, route, error in results:
            if route:
                routes_generated[obj] = route
            elif error:
                errors.append(error)

        if not routes_generated:
            print("ERRORS:", errors)
            # Prioritize specific land errors over generic iteration limits if any
            land_errors = [e for e in errors if "land" in e.lower() or "navigable" in e.lower()]
            if land_errors:
                raise ValueError(land_errors[0])
            if errors:
                raise ValueError(f"Route calculation failed: {errors[0]}")
            raise ValueError("No feasible routes could be generated for comparison.")

        if base_request.objective_type not in routes_generated:
            target_error = next((e for obj, r, e in results if obj == base_request.objective_type and e), None)
            if target_error:
                raise ValueError(target_error)
            
            recommended = next(iter(routes_generated.values()))
        else:
            recommended = routes_generated[base_request.objective_type]

        shortest_route = routes_generated.get(ObjectiveType.SHORTEST, recommended)

        alternatives: List[RouteAlternative] = []
        for obj, route in routes_generated.items():
            if route.properties.route_id == recommended.properties.route_id:
                continue
            time_diff = 0.0
            if route.properties.travel_time is not None and recommended.properties.travel_time is not None:
                time_diff = route.properties.travel_time - recommended.properties.travel_time
            else:
                time_diff = (route.properties.eta - recommended.properties.eta).total_seconds() / 3600.0
                
            risk_diff = 0.0
            if route.properties.risk_exposure is not None and recommended.properties.risk_exposure is not None:
                risk_diff = route.properties.risk_exposure - recommended.properties.risk_exposure
            else:
                risk_diff = route.properties.risk_score - recommended.properties.risk_score

            metrics = RouteComparisonMetrics(
                distance_diff=route.properties.distance - recommended.properties.distance,
                time_diff_hours=time_diff,
                fuel_diff=route.properties.estimated_fuel - recommended.properties.estimated_fuel,
                risk_diff=risk_diff,
            )
            alternatives.append(
                RouteAlternative(route=route, comparison_metrics=metrics)
            )

        explanation = self._generate_explanation(
            recommended.properties,
            shortest_route.properties,
            base_request.objective_type,
        )

        risk_factors = {}
        if recommended.properties.waypoints:
            ice_vals = []
            wave_vals = []
            for wp in recommended.properties.waypoints:
                if wp.env_conditions:
                    if 'sea_ice_concentration' in wp.env_conditions:
                        ice_vals.append(wp.env_conditions['sea_ice_concentration'])
                    if 'wave_height' in wp.env_conditions:
                        wave_vals.append(wp.env_conditions['wave_height'])
            if ice_vals:
                risk_factors["average_sea_ice_concentration"] = float(_avg(ice_vals))
            if wave_vals:
                risk_factors["average_wave_height"] = float(_avg(wave_vals))

        return RouteComparisonResponse(
            recommended_route=recommended,
            alternatives=alternatives,
            optimization_weights=base_request.weights or OptimizationWeights(),
            risk_factors=risk_factors,
            explanation=explanation,
            uncertainty=self._extract_uncertainty(risk_grid),
            warnings=self._get_warnings(risk_grid),
        )
