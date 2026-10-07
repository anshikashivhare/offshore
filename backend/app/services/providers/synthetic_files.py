"""File-backed synthetic data providers.

Loads the bundled synthetic datasets (vessels, ports, risk cells) directly
from the repository files so the API keeps working when PostgreSQL is
unreachable or has no data for a region. The JSON/GeoJSON files are the same
synthetic sets that seed the database (see docs/new_synthetic_seed_report.md).
"""

import json
import logging
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.models.vessel import Vessel

logger = logging.getLogger(__name__)

# backend/app/services/providers/synthetic_files.py -> parents[3] = backend,
# parents[4] = repository root.
_BACKEND_DIR = Path(__file__).resolve().parents[3]
_REPO_ROOT = Path(__file__).resolve().parents[4]

_VESSELS_FILE = _BACKEND_DIR / "data" / "vessels.json"
_PORTS_FILE = _BACKEND_DIR / "data" / "ports.json"
_RISK_CELLS_FILE = _REPO_ROOT / "risk_cells.geojson"

# Columns of the Vessel ORM model; anything else in vessels.json (imo_number,
# mmsi, ...) must be dropped before constructing the model.
_VESSEL_MODEL_FIELDS = {
    "vessel_id",
    "vessel_name",
    "vessel_type",
    "cruising_speed",
    "ice_capability",
    "fuel_consumption",
    "operational_limits",
}


@lru_cache(maxsize=1)
def load_vessels() -> List[Dict[str, Any]]:
    try:
        with _VESSELS_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Synthetic vessels file could not be loaded: %s", exc)
        return []


def vessel_from_record(record: Dict[str, Any], requested_id: Optional[str] = None) -> Optional[Vessel]:
    """Build a Vessel ORM instance from a vessels.json record.

    Ignores JSON-only fields and keeps the requested id when the record is
    used as a fallback for an unknown vessel id.
    """
    try:
        kwargs = {k: v for k, v in record.items() if k in _VESSEL_MODEL_FIELDS}
        if requested_id:
            try:
                kwargs["vessel_id"] = uuid.UUID(str(requested_id))
            except (ValueError, AttributeError):
                pass
        return Vessel(**kwargs)
    except Exception as exc:
        logger.warning("Synthetic vessel record could not be converted: %s", exc)
        return None


def get_vessel_by_id(vessel_id: Any) -> Optional[Vessel]:
    """Resolve a vessel from vessels.json by string id (None when unknown)."""
    records = load_vessels()
    id_str = str(vessel_id)
    record = next((v for v in records if str(v.get("vessel_id")) == id_str), None)
    if record is None:
        return None
    return vessel_from_record(record, requested_id=id_str)


@lru_cache(maxsize=1)
def load_ports() -> List[Dict[str, Any]]:
    try:
        with _PORTS_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Synthetic ports file could not be loaded: %s", exc)
        return []


@lru_cache(maxsize=1)
def _load_risk_cells() -> Tuple[Tuple[float, float, float, float, float], ...]:
    """Load (min_lon, min_lat, max_lon, max_lat, risk) tuples for each cell."""
    try:
        with _RISK_CELLS_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        logger.warning("Synthetic risk cells file could not be loaded: %s", exc)
        return ()

    cells: List[Tuple[float, float, float, float, float]] = []
    for feature in data.get("features", []):
        props = feature.get("properties") or {}
        risk = props.get("risk")
        if risk is None:
            risk = props.get("composite_risk", 0.0)
        geometry = feature.get("geometry") or {}
        coords = geometry.get("coordinates")
        if coords is None:
            continue
        try:
            if geometry.get("type") == "Polygon":
                ring = coords[0]
                lons = [pt[0] for pt in ring]
                lats = [pt[1] for pt in ring]
                cells.append(
                    (min(lons), min(lats), max(lons), max(lats), float(risk))
                )
            elif geometry.get("type") == "Point":
                lon, lat = float(coords[0]), float(coords[1])
                cells.append((lon, lat, lon, lat, float(risk)))
        except (TypeError, ValueError, IndexError):
            continue
    return tuple(cells)


# Matches the 0.1 degree key rasterisation used by the PostGIS-backed grid in
# routes.py so both planners consume an identical structure.
_KEY_STEP = 0.1


def build_synthetic_risk_grid() -> Dict[Tuple[float, float], float]:
    """Rasterise the synthetic risk cells into the planner risk-grid dict."""
    grid: Dict[Tuple[float, float], float] = {}
    for min_lon, min_lat, max_lon, max_lat, risk in _load_risk_cells():
        lat = min_lat
        while lat <= max_lat + 1e-9:
            lon = min_lon
            while lon <= max_lon + 1e-9:
                key = (round(lat, 1), round(lon, 1))
                if risk > grid.get(key, 0.0):
                    grid[key] = risk
                lon += _KEY_STEP
            lat += _KEY_STEP
    return grid
