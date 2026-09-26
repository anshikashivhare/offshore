import json
from typing import Any, Dict, List
from pathlib import Path

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vessel import Vessel
from app.models.iceberg import IcebergDetection
from app.services.providers.interfaces import VesselProvider, PortProvider, IcebergProvider
from app.utils.geojson import to_geojson_geometry

class PostGISVesselProvider(VesselProvider):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_vessel(self, vessel_id: str) -> Dict[str, Any]:
        result = await self.db.execute(select(Vessel).where(Vessel.vessel_id == vessel_id))
        vessel = result.scalars().first()
        if not vessel:
            raise ValueError(f"Vessel {vessel_id} not found")
        return {
            "vessel_id": str(vessel.vessel_id),
            "vessel_name": vessel.vessel_name,
            "max_speed_knots": vessel.cruising_speed,
            "draft_m": 8.0, # default or from operational_limits
            "source": "postgres"
        }

class JSONPortProvider(PortProvider):
    def __init__(self):
        self.ports = []
        try:
            ports_path = Path(__file__).resolve().parents[3] / "data" / "ports.json"
            if ports_path.exists():
                with ports_path.open("r", encoding="utf-8") as f:
                    self.ports = json.load(f)
        except Exception:
            pass

    async def get_port(self, port_id: str) -> Dict[str, Any]:
        for p in self.ports:
            if str(p.get("port_id")) == port_id:
                p["source"] = "json"
                return p
        raise ValueError(f"Port {port_id} not found")

class PostGISIcebergProvider(IcebergProvider):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_candidate_icebergs(self, bounds: Dict[str, float], start_time: Any = None, end_time: Any = None) -> List[Dict[str, Any]]:
        # ST_MakeEnvelope(xmin, ymin, xmax, ymax, srid)
        # WGS84 is lon, lat -> x, y
        envelope = func.ST_MakeEnvelope(
            bounds["min_lon"], bounds["min_lat"],
            bounds["max_lon"], bounds["max_lat"],
            4326
        )
        stmt = select(IcebergDetection).where(IcebergDetection.geometry.ST_Intersects(envelope))
        
        # We could also filter by time if start_time/end_time are provided
        if start_time:
            stmt = stmt.where(IcebergDetection.timestamp >= start_time)
        if end_time:
            stmt = stmt.where(IcebergDetection.timestamp <= end_time)
            
        stmt = stmt.order_by(IcebergDetection.timestamp.desc()).limit(1000)
        
        result = await self.db.execute(stmt)
        detections = result.scalars().all()
        
        candidates = []
        for d in detections:
            geom = to_geojson_geometry(d.geometry)
            coords = geom.get("coordinates")
            if coords and geom.get("type") == "Point":
                candidates.append({
                    "iceberg_id": str(d.iceberg_id),
                    "lat": coords[1],
                    "lon": coords[0],
                    "timestamp": d.timestamp,
                    "source": "postgres"
                })
        return candidates
