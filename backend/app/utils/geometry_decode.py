"""Decode GeoAlchemy2 geometry values into a (lon, lat) centroid."""

from __future__ import annotations

import re
from typing import Optional, Tuple


def geometry_centroid_lonlat(value) -> Optional[Tuple[float, float]]:
    """Best-effort extract a (lon, lat) pair from a GeoAlchemy2 geometry.

    Tries, in order:
      1. ``.centroid`` if the value is already a Shapely-like object
      2. ``.coords[0]`` for shapely Point-like
      3. ``ST_AsGeoJSON`` SQL-side decoding via ``.data`` attribute
      4. WKT parsing of ``.data`` or stringified value

    Returns ``None`` when the geometry cannot be decoded.
    """
    if value is None:
        return None
    # Already a Shapely geometry
    if hasattr(value, "centroid"):
        try:
            c = value.centroid
            if c is not None and hasattr(c, "x") and hasattr(c, "y"):
                return float(c.x), float(c.y)
        except Exception:
            pass
    if hasattr(value, "x") and hasattr(value, "y"):
        try:
            return float(value.x), float(value.y)
        except Exception:
            pass
    # Try GeoJSON via .data (WKB hex) — fallback to WKT text
    if hasattr(value, "data"):
        try:
            text = (
                value.data
                if isinstance(value.data, str)
                else value.data.decode("utf-8", errors="ignore")
            )
        except Exception:
            text = None
        if text and text.lstrip().upper().startswith(
            ("POINT", "LINESTRING", "POLYGON")
        ):
            return _wkt_centroid(text)
    text = str(value) if not isinstance(value, str) else value
    return _wkt_centroid(text)


def _wkt_centroid(wkt: str) -> Optional[Tuple[float, float]]:
    if not wkt:
        return None
    s = wkt.strip().upper()
    # POINT(x y) -> use x,y directly
    m = re.match(r"^POINT\s*\(\s*([-\d.eE+]+)\s+([-\d.eE+]+)\s*\)", s)
    if m:
        try:
            return float(m.group(1)), float(m.group(2))
        except ValueError:
            return None
    # LINESTRING(x1 y1, x2 y2, ...) -> mean of endpoints
    m = re.match(r"^LINESTRING\s*\((.*)\)$", s, re.DOTALL)
    if m:
        coords = re.findall(r"([-\d.eE+]+)\s+([-\d.eE+]+)", m.group(1))
        if not coords:
            return None
        try:
            xs = [float(x) for x, _ in coords]
            ys = [float(y) for _, y in coords]
            return sum(xs) / len(xs), sum(ys) / len(ys)
        except ValueError:
            return None
    # POLYGON((x1 y1, ..., x1 y1)) -> mean of first ring
    m = re.match(r"^POLYGON\s*\(\((.*)\)\)\s*$", s, re.DOTALL)
    if m:
        coords = re.findall(r"([-\d.eE+]+)\s+([-\d.eE+]+)", m.group(1))
        if not coords:
            return None
        try:
            xs = [float(x) for x, _ in coords]
            ys = [float(y) for _, y in coords]
            return sum(xs) / len(xs), sum(ys) / len(ys)
        except ValueError:
            return None
    return None
