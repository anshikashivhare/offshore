"""Route validation layer for ensuring land-free routes.

This module provides comprehensive validation that routes do not cross land masses.
It verifies both waypoints and segments between waypoints using dense sampling.
"""
import math
from typing import List, Optional, Tuple
from global_land_mask import globe

from app.services.routing.grid import Node


class RouteValidationError(Exception):
    """Raised when a route fails land avoidance validation."""
    pass


class RouteValidator:
    """Validates that generated routes remain in navigable water."""

    def __init__(self, segment_sample_resolution: float = 0.05):
        """Initialize validator.

        Args:
            segment_sample_resolution: Degrees between samples when checking segments (default 0.05° ≈ 5km)
        """
        self.segment_sample_resolution = segment_sample_resolution

    def validate_route_geometry(
        self,
        waypoints: List[Node],
        strict: bool = True
    ) -> Tuple[bool, Optional[str], Optional[dict]]:
        """Validate that a route does not cross land.

        Performs two checks:
        1. Every waypoint is in water
        2. Every segment between consecutive waypoints doesn't cross land (dense sampling)

        Args:
            waypoints: List of route waypoints to validate
            strict: If True, raise exception on failure. If False, return result tuple.

        Returns:
            Tuple of (is_valid, error_message, failure_details)
            - is_valid: True if route passes all checks
            - error_message: Human-readable error message if validation fails
            - failure_details: Dict with specific failure information

        Raises:
            RouteValidationError: If strict=True and validation fails
        """
        if not waypoints:
            msg = "Route has no waypoints"
            if strict:
                raise RouteValidationError(msg)
            return False, msg, {"type": "empty_route"}

        # Check 1: Verify all waypoints are in water
        for idx, wp in enumerate(waypoints):
            if globe.is_land(wp.lat, wp.lon):
                msg = f"Waypoint {idx} at ({wp.lat:.4f}, {wp.lon:.4f}) is on land"
                details = {
                    "type": "waypoint_on_land",
                    "waypoint_index": idx,
                    "lat": wp.lat,
                    "lon": wp.lon
                }
                if strict:
                    raise RouteValidationError(msg)
                return False, msg, details

        # Check 2: Verify segments between waypoints don't cross land
        for idx in range(len(waypoints) - 1):
            wp1 = waypoints[idx]
            wp2 = waypoints[idx + 1]

            # Calculate segment length and sample it densely
            dlat = wp2.lat - wp1.lat
            dlon = wp2.lon - wp1.lon

            # Handle antimeridian crossing (use shortest path)
            if dlon > 180:
                dlon -= 360
            elif dlon < -180:
                dlon += 360

            dist_deg = math.sqrt(dlat**2 + dlon**2)
            samples = max(5, int(math.ceil(dist_deg / self.segment_sample_resolution)))

            # Sample along the segment (excluding start point which was already validated)
            for j in range(1, samples + 1):
                t = j / float(samples)
                test_lat = wp1.lat + t * dlat
                test_lon = wp1.lon + t * dlon

                # Wrap longitude
                if test_lon > 180:
                    test_lon -= 360
                elif test_lon < -180:
                    test_lon += 360

                if globe.is_land(test_lat, test_lon):
                    msg = (
                        f"Segment from waypoint {idx} ({wp1.lat:.4f}, {wp1.lon:.4f}) "
                        f"to waypoint {idx+1} ({wp2.lat:.4f}, {wp2.lon:.4f}) "
                        f"crosses land at ({test_lat:.4f}, {test_lon:.4f})"
                    )
                    details = {
                        "type": "segment_crosses_land",
                        "segment_start_index": idx,
                        "segment_end_index": idx + 1,
                        "start_lat": wp1.lat,
                        "start_lon": wp1.lon,
                        "end_lat": wp2.lat,
                        "end_lon": wp2.lon,
                        "land_crossing_lat": test_lat,
                        "land_crossing_lon": test_lon,
                        "sample_position": t
                    }
                    if strict:
                        raise RouteValidationError(msg)
                    return False, msg, details

        return True, None, None

    def validate_wkt_linestring(
        self,
        wkt_geometry: str,
        strict: bool = True
    ) -> Tuple[bool, Optional[str], Optional[dict]]:
        """Validate a WKT LINESTRING geometry for land avoidance.

        Args:
            wkt_geometry: WKT LINESTRING format "LINESTRING(lon1 lat1, lon2 lat2, ...)"
            strict: If True, raise exception on failure

        Returns:
            Tuple of (is_valid, error_message, failure_details)
        """
        # Parse WKT LINESTRING
        if not wkt_geometry.startswith("LINESTRING(") or not wkt_geometry.endswith(")"):
            msg = "Invalid WKT LINESTRING format"
            if strict:
                raise RouteValidationError(msg)
            return False, msg, {"type": "invalid_wkt"}

        coords_str = wkt_geometry[11:-1]  # Remove "LINESTRING(" and ")"
        coord_pairs = coords_str.split(", ")

        waypoints = []
        for pair in coord_pairs:
            try:
                lon, lat = map(float, pair.split())
                waypoints.append(Node(lat=lat, lon=lon))
            except (ValueError, IndexError):
                msg = f"Invalid coordinate pair: {pair}"
                if strict:
                    raise RouteValidationError(msg)
                return False, msg, {"type": "invalid_coordinates", "pair": pair}

        return self.validate_route_geometry(waypoints, strict=strict)


# Global validator instance
route_validator = RouteValidator()
