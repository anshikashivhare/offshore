import json
import logging
from pathlib import Path

from fastapi import APIRouter, Query, Depends
from typing import List
from pydantic import BaseModel
from app.api.dependencies.cache import cache_response, clear_cache_for_prefix

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/reload", response_model=bool)
def reload_ports():
    """Reload ports JSON file and invalidate related caches."""
    global PORTS_DATA
    try:
        with _ports_path.open("r", encoding="utf-8") as f:
            PORTS_DATA = json.load(f)
        # Invalidate cache for both list and search endpoints
        clear_cache_for_prefix("/api/v1/ports")
        return True
    except Exception as exc:
        logger.error("Failed to reload ports data: %s", exc)
        return False


from app.api import deps
from app.schemas.common import Pagination


class Port(BaseModel):
    name: str
    country: str
    lat: float
    lon: float

# Load ports data once at module import using pathlib for clarity
_ports_path = Path(__file__).resolve().parents[4] / "data" / "ports.json"
try:
    with _ports_path.open("r", encoding="utf-8") as f:
        PORTS_DATA = json.load(f)
except Exception as exc:
    logger.error("Failed to load ports data: %s", exc)
    PORTS_DATA = []


@router.get("/", response_model=Pagination[Port])
def get_ports(
    pagination: deps.PaginationParams = Depends(),
    bbox: deps.BBoxParams = Depends()
):
    """Return a paginated list of ports, optionally filtered by bounding box."""
    results = PORTS_DATA
    bbox_tuple = bbox.as_tuple()
    if bbox_tuple:
        min_lat, min_lon, max_lat, max_lon = bbox_tuple
        results = [
            p for p in results
            if min_lat <= p["lat"] <= max_lat and min_lon <= p["lon"] <= max_lon
        ]
    return Pagination.from_list(results, pagination.skip, pagination.limit)


@router.get("/search", response_model=Pagination[Port])
def search_ports(
    q: str = Query(..., min_length=1),
    pagination: deps.PaginationParams = Depends(),
):
    """Search ports by name or country substring (case‑insensitive) with pagination."""
    q_lower = q.lower()
    results = [p for p in PORTS_DATA if q_lower in p["name"].lower() or q_lower in p["country"].lower()]
    return Pagination.from_list(results, pagination.skip, pagination.limit)
