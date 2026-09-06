"""Geometry helpers for converting SQLAlchemy GeoAlchemy2 values to GeoJSON."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

# WKT LINESTRING parser (sufficient for the simple, well-formed output produced
# by the routing engine and acceptable for our backend's geometry payloads).
_LINESTRING_RE = re.compile(r"LINESTRING\s*\(([^)]+)\)", re.IGNORECASE)
_POINT_RE = re.compile(r"POINT\s*\(([^)]+)\)", re.IGNORECASE)
_POLYGON_RE = re.compile(r"POLYGON\s*\((.*)\)$", re.IGNORECASE | re.DOTALL)


def _to_float_pair(token: str) -> Tuple[float, float]:
    parts = token.replace(",", " ").split()
    if len(parts) < 2:
        raise ValueError(f"Invalid coordinate pair: {token!r}")
    return float(parts[0]), float(parts[1])


def parse_wkt_point(wkt: str) -> Dict[str, Any]:
    m = _POINT_RE.search(wkt)
    if not m:
        raise ValueError(f"Not a POINT: {wkt!r}")
    lon, lat = _to_float_pair(m.group(1))
    return {"type": "Point", "coordinates": [lon, lat]}


def parse_wkt_linestring(wkt: str) -> Dict[str, Any]:
    m = _LINESTRING_RE.search(wkt)
    if not m:
        raise ValueError(f"Not a LINESTRING: {wkt!r}")
    coords: List[List[float]] = []
    for token in m.group(1).split(","):
        lon, lat = _to_float_pair(token)
        coords.append([lon, lat])
    return {"type": "LineString", "coordinates": coords}


def parse_wkt_polygon(wkt: str) -> Dict[str, Any]:
    m = _POLYGON_RE.search(wkt.strip())
    if not m:
        raise ValueError(f"Not a POLYGON: {wkt!r}")
    body = m.group(1).strip()
    rings: List[List[List[float]]] = []
    depth = 0
    current: List[str] = []
    for ch in body:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
            if depth == 0:
                rings.append("".join(current).strip("()"))
                current = []
        elif ch == "," and depth == 0:
            continue
        else:
            current.append(ch)
    if current:
        rings.append("".join(current).strip())
    coords: List[List[List[float]]] = []
    for ring in rings:
        ring_coords: List[List[float]] = []
        for token in ring.split(","):
            lon, lat = _to_float_pair(token)
            ring_coords.append([lon, lat])
        coords.append(ring_coords)
    return {"type": "Polygon", "coordinates": coords}


def to_geojson_geometry(value: Any) -> Dict[str, Any]:
    """Convert a model geometry attribute (WKT string) to a GeoJSON dict.

    Falls back to a 0,0 Point when the geometry is missing or unparseable so
    the API still returns a valid GeoJSON envelope; downstream code that cares
    about correctness should validate the geometry separately.
    """
    fallback = {"type": "Point", "coordinates": [0.0, 0.0]}
    if value is None:
        return fallback
    text: Optional[str]
    if isinstance(value, str):
        text = value
    elif hasattr(value, "data") and isinstance(value.data, str):
        text = value.data
    elif hasattr(value, "wkt") and isinstance(value.wkt, str):
        text = value.wkt
    else:
        text = str(value)
    try:
        if text.upper().lstrip().startswith("POINT"):
            return parse_wkt_point(text)
        if text.upper().lstrip().startswith("LINESTRING"):
            return parse_wkt_linestring(text)
        if text.upper().lstrip().startswith("POLYGON"):
            return parse_wkt_polygon(text)
    except Exception:
        return fallback
    return fallback