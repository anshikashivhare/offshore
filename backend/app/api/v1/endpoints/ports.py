import json
import logging
from pathlib import Path

from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from pydantic import BaseModel
from app.api.dependencies.cache import cache_response, clear_cache_for_prefix

logger = logging.getLogger(__name__)

router = APIRouter()


class Port(BaseModel):
    id: Optional[str] = None
    name: str
    country: str
    lat: float
    lon: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None


def _normalize_port(p: dict, idx: int) -> dict:
    lat = float(p.get("lat") if "lat" in p else p.get("latitude", 0.0))
    lon = float(p.get("lon") if "lon" in p else p.get("longitude", 0.0))
    port_id = str(p.get("id") or f"port-{idx}")
    return {
        "id": port_id,
        "name": p.get("name", "Unknown"),
        "country": p.get("country", ""),
        "lat": lat,
        "lon": lon,
        "latitude": lat,
        "longitude": lon,
    }


def _synthetic_ports() -> List[dict]:
    """Bundled synthetic ports (backend/data/ports.json), DB-shaped."""
    from app.config.config import settings
    if not getattr(settings, "SYNTHETIC_DATA_MODE", False):
        return []
    from app.services.providers.synthetic_files import load_ports
    return [
        _normalize_port(p, idx)
        for idx, p in enumerate(load_ports())
    ]


import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.schemas.common import Pagination

@router.get("", response_model=Pagination[Port])
@router.get("/", response_model=Pagination[Port])
async def get_ports(
    pagination: deps.PaginationParams = Depends(),
    bbox: deps.BBoxParams = Depends(),
    db: AsyncSession = Depends(deps.get_db)
):
    """Return a paginated list of ports, optionally filtered by bounding box."""
    bbox_tuple = bbox.as_tuple()
    where_clause = ""
    params = {}
    if bbox_tuple:
        min_lat, min_lon, max_lat, max_lon = bbox_tuple
        where_clause = "WHERE latitude >= :min_lat AND latitude <= :max_lat AND longitude >= :min_lon AND longitude <= :max_lon"
        params = {"min_lat": min_lat, "max_lat": max_lat, "min_lon": min_lon, "max_lon": max_lon}
        
    query = f"SELECT port_id, name, country, latitude, longitude FROM ports {where_clause} ORDER BY name LIMIT :limit OFFSET :skip"
    params["limit"] = pagination.limit
    params["skip"] = pagination.skip

    try:
        res = await db.execute(text(query), params)
    except Exception:
        # Database unavailable - serve the bundled synthetic ports instead.
        ports = _synthetic_ports()
        if bbox_tuple:
            min_lat, min_lon, max_lat, max_lon = bbox_tuple
            ports = [
                p for p in ports
                if min_lat <= p["lat"] <= max_lat and min_lon <= p["lon"] <= max_lon
            ]
        ports.sort(key=lambda p: p["name"])
        return Pagination.from_list(ports, pagination.skip, pagination.limit)
    results = []
    for r in res:
        results.append({
            "id": str(r.port_id),
            "name": r.name,
            "country": r.country,
            "lat": r.latitude,
            "lon": r.longitude,
            "latitude": r.latitude,
            "longitude": r.longitude
        })
    return Pagination.from_list(results, 0, len(results))


@router.get("/search", response_model=Pagination[Port])
async def search_ports(
    q: str = Query(..., min_length=1),
    pagination: deps.PaginationParams = Depends(),
    db: AsyncSession = Depends(deps.get_db)
):
    """Search ports by name or country substring (case‑insensitive) with pagination."""
    query = "SELECT port_id, name, country, latitude, longitude FROM ports WHERE name ILIKE :q OR country ILIKE :q ORDER BY name LIMIT :limit OFFSET :skip"
    try:
        res = await db.execute(text(query), {"q": f"%{q}%", "limit": pagination.limit, "skip": pagination.skip})
    except Exception:
        # Database unavailable - search the bundled synthetic ports instead.
        q_lower = q.lower()
        ports = [
            p for p in _synthetic_ports()
            if q_lower in p["name"].lower() or q_lower in p["country"].lower()
        ]
        ports.sort(key=lambda p: p["name"])
        return Pagination.from_list(ports, pagination.skip, pagination.limit)
    results = []
    for r in res:
        results.append({
            "id": str(r.port_id),
            "name": r.name,
            "country": r.country,
            "lat": r.latitude,
            "lon": r.longitude,
            "latitude": r.latitude,
            "longitude": r.longitude
        })
    return Pagination.from_list(results, 0, len(results))
