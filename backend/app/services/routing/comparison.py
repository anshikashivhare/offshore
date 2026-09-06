from __future__ import annotations

import copy
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.enums import ObjectiveType
from app.models.vessel import Vessel
from app.schemas.route import (
    OptimizationWeights,
    RouteAlternative,
    RouteComparisonMetrics,
    RouteComparisonResponse,
    RouteCreate,
    RouteProperties,
    RouteRequest,
    RouteResponse,
)
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
        time_diff = (recommended.eta - shortest.eta).total_seconds() / 3600.0
        fuel_diff = recommended.estimated_fuel - shortest.estimated_fuel
        risk_diff = recommended.risk_score - shortest.risk_score

        parts = [f"This route was recommended because the objective is {objective.value.upper()}."]
        if risk_diff < -0.01:
            parts.append(
                f"It significantly reduces risk exposure compared to the shortest path (by {-risk_diff:.2f})."
            )
        elif risk_diff > 0.01:
            parts.append(f"It accepts higher risk (by {risk_diff:.2f}) to achieve other goals.")
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
        if not risk_grid:
            return "Risk surface unavailable. Recommendation based on geometric distance only."
        confidences: List[float] = []
        for v in risk_grid.values():
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
            return f"High confidence (avg={avg:.2f}). Risk-aware pathfinding is reliable."
        if avg >= 0.5:
            return f"Medium confidence (avg={avg:.2f}). Forecasts have moderate variance."
        return f"Low confidence (avg={avg:.2f}). Treat risk values as indicative only."

    def _get_warnings(self, risk_grid: Any) -> List[str]:
        warnings: List[str] = []
        if not risk_grid:
            warnings.append("Risk surface empty; route based on geometric shortest path.")
            return warnings
        high = 0
        for v in risk_grid.values():
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
            eta=route_create.eta,
            estimated_fuel=route_create.estimated_fuel,
            risk_score=route_create.risk_score,
            objective_type=route_create.objective_type,
            algorithm_version=route_create.algorithm_version,
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
        objectives = [
            ObjectiveType.SHORTEST,
            ObjectiveType.FASTEST,
            ObjectiveType.SAFEST,
            ObjectiveType.FUEL_EFFICIENT,
        ]
        if base_request.objective_type not in objectives:
            objectives.append(base_request.objective_type)

        routes_generated: Dict[ObjectiveType, RouteResponse] = {}

        for obj in objectives:
            req = copy.deepcopy(base_request)
            req.objective_type = obj
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
                routes_generated[obj] = self._convert_to_response(route_create)
            except ValueError:
                continue
            except Exception:
                continue

        if not routes_generated:
            raise ValueError("No feasible routes could be generated for comparison.")

        if base_request.objective_type in routes_generated:
            recommended = routes_generated[base_request.objective_type]
        else:
            recommended = next(iter(routes_generated.values()))

        shortest_route = routes_generated.get(ObjectiveType.SHORTEST, recommended)

        alternatives: List[RouteAlternative] = []
        for obj, route in routes_generated.items():
            if route.properties.route_id == recommended.properties.route_id:
                continue
            metrics = RouteComparisonMetrics(
                distance_diff=route.properties.distance - recommended.properties.distance,
                time_diff_hours=(
                    route.properties.eta - recommended.properties.eta
                ).total_seconds() / 3600.0,
                fuel_diff=route.properties.estimated_fuel - recommended.properties.estimated_fuel,
                risk_diff=route.properties.risk_score - recommended.properties.risk_score,
            )
            alternatives.append(RouteAlternative(route=route, comparison_metrics=metrics))

        explanation = self._generate_explanation(
            recommended.properties, shortest_route.properties, base_request.objective_type
        )

        contributing = {
            "iceberg_exposure": float(recommended.properties.risk_score),
            "weather_severity": float(recommended.properties.risk_score),
        }

        return RouteComparisonResponse(
            recommended_route=recommended,
            alternatives=alternatives,
            optimization_weights=base_request.weights or OptimizationWeights(),
            contributing_risk_factors=contributing,
            explanation=explanation,
            uncertainty=self._extract_uncertainty(risk_grid),
            warnings=self._get_warnings(risk_grid),
        )