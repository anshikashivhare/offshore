from __future__ import annotations

import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.models.enums import AlertSeverity
from app.models.route import Route
from app.schemas.alert import AlertCreate
from app.utils.geojson import parse_wkt_linestring

logger = logging.getLogger(__name__)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2.0) ** 2
    )
    return 2.0 * 6371.0088 * math.asin(min(1.0, math.sqrt(a)))


def haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    return haversine_km(lat1, lon1, lat2, lon2) / 1.852


class AlertEngine:
    def __init__(
        self,
        thresholds: Optional[Dict[str, float]] = None,
        proximity_buffer_nm: float = 30.0,
        intersect_threshold_nm: float = 5.0,
        proximity_buffer_deg: Optional[float] = None,
        intersect_threshold_deg: Optional[float] = None,
    ):
        """Initialize the alert engine.

        Distances default to nautical miles. ``proximity_buffer_deg`` /
        ``intersect_threshold_deg`` (degrees) are accepted for backwards
        compatibility with tests and may be supplied instead of the NM values.
        """
        self.thresholds = thresholds or {
            "sea_ice": 0.7,
            "iceberg": 0.6,
            "weather": 0.8,
            "current": 0.9,
            "combined": 0.75,
        }
        if proximity_buffer_deg is not None:
            self.proximity_buffer_nm = haversine_nm(0.0, 0.0, proximity_buffer_deg, 0.0)
        else:
            self.proximity_buffer_nm = proximity_buffer_nm
        if intersect_threshold_deg is not None:
            self.intersect_threshold_nm = haversine_nm(0.0, 0.0, intersect_threshold_deg, 0.0)
        else:
            self.intersect_threshold_nm = intersect_threshold_nm

    def _determine_severity(self, metric: float, threshold: float) -> AlertSeverity:
        if metric >= threshold + 0.2 or metric >= 0.9:
            return AlertSeverity.CRITICAL
        if metric >= threshold:
            return AlertSeverity.HIGH
        if metric >= threshold - 0.2:
            return AlertSeverity.MEDIUM
        return AlertSeverity.LOW

    def _generate_message(
        self, hazard_type: str, severity: AlertSeverity, metric: float, intersect: bool
    ) -> str:
        if metric < 0:
            return f"Missing prediction data for {hazard_type} along the planned route."
        action = "intersects" if intersect else "approaches within proximity buffer of"
        return (
            f"Predicted {severity.value} {hazard_type} hazard region {action} "
            "the planned route."
        )

    def _haversine_nm(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        return haversine_nm(lat1, lon1, lat2, lon2)

    def _check_proximity(
        self, route_points: List[Tuple[float, float]], hazard_lat: float, hazard_lon: float
    ) -> Tuple[bool, bool, float]:
        """Return (is_intersecting, is_proximate, min_distance_nm)."""
        is_intersecting = False
        is_proximate = False
        min_d = float("inf")
        for lat, lon in route_points:
            d = self._haversine_nm(lat, lon, hazard_lat, hazard_lon)
            if d < min_d:
                min_d = d
            if d <= self.intersect_threshold_nm:
                is_intersecting = True
            elif d <= self.proximity_buffer_nm:
                is_proximate = True
        return is_intersecting, is_proximate, min_d

    def evaluate_route(
        self, route: Route, risk_grid: Dict[Any, Any]
    ) -> List[AlertCreate]:
        alerts: List[AlertCreate] = []

        route_points: List[Tuple[float, float]] = []
        try:
            geometry = parse_wkt_linestring(route.geometry or "")
            for lon, lat in geometry.get("coordinates", []):
                route_points.append((float(lat), float(lon)))
        except Exception:
            pass

        if not route_points:
            try:
                origin_coords = [float(x) for x in route.origin.split(",")]
                dest_coords = [float(x) for x in route.destination.split(",")]
                route_points = [
                    (origin_coords[1], origin_coords[0]),
                    (dest_coords[1], dest_coords[0]),
                ]
            except Exception:
                route_points = [(0.0, 0.0), (0.0, 0.0)]

        if not risk_grid:
            alerts.append(
                AlertCreate(
                    alert_type="missing_data",
                    severity=AlertSeverity.MEDIUM,
                    location=f"POINT({route_points[0][1]} {route_points[0][0]})",
                    timestamp=datetime.now(timezone.utc),
                    route_id=route.route_id,
                    hazard_source="system",
                    message=self._generate_message(
                        "environmental data", AlertSeverity.MEDIUM, -1.0, True
                    ),
                    triggering_metric=-1.0,
                    threshold=0.0,
                    confidence=0.0,
                )
            )
            return alerts

        for key, risks in risk_grid.items():
            # Normalize key to (lat, lon). Convention: orchestrator already uses (lat, lon) tuples.
            if isinstance(key, (list, tuple)) and len(key) == 2:
                hazard_lat, hazard_lon = float(key[0]), float(key[1])
            elif isinstance(key, str) and "," in key:
                parts = [float(p) for p in key.split(",")]
                hazard_lat, hazard_lon = parts[0], parts[1]
            else:
                continue

            is_intersecting, is_proximate, _ = self._check_proximity(
                route_points, hazard_lat, hazard_lon
            )
            if not is_intersecting and not is_proximate:
                continue

            # Risks can be either:
            # - dict of hazard_name -> value (per-component), or
            # - scalar (treated as composite risk).
            if isinstance(risks, dict):
                risk_items = list(risks.items())
            else:
                risk_items = [("combined", float(risks))]

            for hazard_type, metric in risk_items:
                threshold = self.thresholds.get(hazard_type, 0.7)
                if metric >= threshold:
                    severity = self._determine_severity(float(metric), threshold)
                    message = self._generate_message(
                        hazard_type, severity, float(metric), is_intersecting
                    )
                    # GeoJSON convention: [lon, lat]
                    alerts.append(
                        AlertCreate(
                            alert_type=hazard_type,
                            severity=severity,
                            location=f"POINT({hazard_lon} {hazard_lat})",
                            timestamp=datetime.now(timezone.utc),
                            route_id=route.route_id,
                            hazard_source=f"{hazard_type}_model",
                            message=message,
                            triggering_metric=float(metric),
                            threshold=threshold,
                            confidence=min(1.0, 0.5 + 0.5 * float(metric)),
                        )
                    )

        return alerts