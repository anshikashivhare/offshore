"""WGS84 coordinate contract used by all public route inputs.

The API accepts longitude/latitude pairs in GeoJSON order: ``"lon,lat"``.
Keeping this check in one place prevents a display or routing caller from
silently treating projected metres or a latitude/longitude pair as WGS84.
"""

from typing import Tuple


def parse_wgs84_lon_lat(value: str) -> Tuple[float, float]:
    """Return a validated ``(longitude, latitude)`` pair in EPSG:4326.

    EPSG:4326 is a geographic CRS expressed in decimal degrees.  Coordinate
    reference systems are deliberately not guessed: callers with projected
    data must transform it before using this API.
    """
    if not isinstance(value, str):
        raise ValueError("Coordinate must be a 'longitude,latitude' string in EPSG:4326.")

    parts = value.split(",")
    if len(parts) != 2:
        raise ValueError("Coordinate must be 'longitude,latitude' in EPSG:4326.")

    try:
        longitude, latitude = (float(part.strip()) for part in parts)
    except ValueError as exc:
        raise ValueError("Longitude and latitude must be decimal degrees.") from exc

    if not -180.0 <= longitude <= 180.0:
        raise ValueError("Longitude must be within [-180, 180] degrees (EPSG:4326).")
    if not -90.0 <= latitude <= 90.0:
        raise ValueError("Latitude must be within [-90, 90] degrees (EPSG:4326).")

    return longitude, latitude
