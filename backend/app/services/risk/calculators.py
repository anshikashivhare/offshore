"""Risk calculators that read from real observation tables."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.iceberg import IcebergDetection
from app.models.observation import (
    OceanObservation,
    SeaIceObservation,
    WeatherObservation,
)
from app.utils.geometry_decode import geometry_centroid_lonlat


class RiskComponentResult(BaseModel):
    risk_value: float
    confidence: float
    is_missing: bool
    metadata: Dict[str, Any] = {}


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    r = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2.0) ** 2
    )
    return 2.0 * r * math.asin(min(1.0, math.sqrt(a)))


def _nearby_query(model, lat: float, lon: float, *, envelope_deg: float = 3.0, limit: int = 20):
    """Return a SQLAlchemy select for nearby rows of ``model``.

    Falls back to returning all rows (limited) when the geometry column has
    been monkey-patched to a non-spatial type (e.g., SQLite tests).
    """
    geom = getattr(model, "geometry", None)
    if geom is not None:
        st_intersects = getattr(geom, "ST_Intersects", None)
        if st_intersects is not None:
            envelope = func.ST_MakeEnvelope(
                lon - envelope_deg,
                lat - envelope_deg,
                lon + envelope_deg,
                lat + envelope_deg,
                4326,
            )
            stmt = select(model).where(st_intersects(envelope))
            ts = getattr(model, "timestamp", None)
            if ts is not None:
                stmt = stmt.order_by(ts.desc())
            return stmt.limit(limit)
    return select(model).limit(limit)


def _centroid_or_none(geom_value: Any) -> Optional[tuple]:
    return geometry_centroid_lonlat(geom_value)


class RiskCalculator(ABC):
    """Base class for all environmental risk components."""

    @abstractmethod
    async def calculate(
        self, lat: float, lon: float, timestamp: Any
    ) -> RiskComponentResult: ...


class IceRiskCalculator(RiskCalculator):
    """Reads ``SeaIceObservation.concentration`` within a search radius."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        search_radius_km: float = 100.0,
        influence_radius_km: float = 250.0,
    ):
        self.db = db
        self.search_radius_km = search_radius_km
        self.influence_radius_km = influence_radius_km

    async def calculate(
        self, lat: float, lon: float, timestamp: Any
    ) -> RiskComponentResult:
        stmt = _nearby_query(SeaIceObservation, lat, lon)
        rows = (await self.db.execute(stmt)).scalars().all()
        if not rows:
            return RiskComponentResult(
                risk_value=0.0, confidence=0.0, is_missing=True,
                metadata={"source": "sea_ice_obs", "nearest_km": None},
            )
        best = None
        best_d = float("inf")
        for row in rows:
            coord = _centroid_or_none(row.geometry)
            if coord is None:
                continue
            lon0, lat0 = coord
            d = haversine_km(lat, lon, lat0, lon0)
            if d < best_d:
                best = row
                best_d = d
        if best is None or best_d > self.influence_radius_km:
            return RiskComponentResult(
                risk_value=0.0,
                confidence=0.2 if best is not None else 0.0,
                is_missing=best is None,
                metadata={
                    "source": "sea_ice_obs",
                    "nearest_km": None if best is None else round(best_d, 1),
                },
            )
        distance_factor = max(0.0, 1.0 - best_d / self.influence_radius_km)
        risk = max(0.0, min(1.0, float(best.concentration) * distance_factor))
        return RiskComponentResult(
            risk_value=risk,
            confidence=min(1.0, distance_factor * (best.data_quality or 0.8)),
            is_missing=False,
            metadata={
                "source": "sea_ice_obs",
                "observation_id": str(best.id),
                "nearest_km": round(best_d, 1),
                "concentration": best.concentration,
                "data_quality": best.data_quality,
            },
        )


class IcebergRiskCalculator(RiskCalculator):
    """Reads ``IcebergDetection`` rows and decays risk with distance."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        influence_radius_km: float = 75.0,
    ):
        self.db = db
        self.influence_radius_km = influence_radius_km

    async def calculate(
        self, lat: float, lon: float, timestamp: Any
    ) -> RiskComponentResult:
        stmt = _nearby_query(IcebergDetection, lat, lon)
        rows = (await self.db.execute(stmt)).scalars().all()
        if not rows:
            return RiskComponentResult(
                risk_value=0.0, confidence=0.0, is_missing=True,
                metadata={"source": "iceberg_detection", "nearest_km": None},
            )
        contributions = []
        for row in rows:
            coord = _centroid_or_none(row.geometry)
            if coord is None:
                continue
            lon0, lat0 = coord
            d = haversine_km(lat, lon, lat0, lon0)
            if d > self.influence_radius_km:
                continue
            decay = max(0.0, 1.0 - d / self.influence_radius_km)
            conf = float(row.confidence or 0.5)
            contributions.append(decay * conf)
        if not contributions:
            return RiskComponentResult(
                risk_value=0.0,
                confidence=0.1,
                is_missing=False,
                metadata={
                    "source": "iceberg_detection",
                    "nearest_km": "outside_radius",
                },
            )
        risk = max(0.0, min(1.0, max(contributions)))
        return RiskComponentResult(
            risk_value=risk,
            confidence=min(1.0, max(contributions)),
            is_missing=False,
            metadata={
                "source": "iceberg_detection",
                "n_contributing": len(contributions),
                "influence_radius_km": self.influence_radius_km,
            },
        )


class WeatherRiskCalculator(RiskCalculator):
    """Combines wind speed and wave height into a single risk value."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        search_radius_km: float = 150.0,
    ):
        self.db = db
        self.search_radius_km = search_radius_km

    async def calculate(
        self, lat: float, lon: float, timestamp: Any
    ) -> RiskComponentResult:
        stmt = _nearby_query(WeatherObservation, lat, lon)
        rows = (await self.db.execute(stmt)).scalars().all()
        if not rows:
            return RiskComponentResult(
                risk_value=0.0, confidence=0.0, is_missing=True,
                metadata={"source": "weather_obs"},
            )
        best = None
        best_d = float("inf")
        for row in rows:
            coord = _centroid_or_none(row.geometry)
            if coord is None:
                continue
            lon0, lat0 = coord
            d = haversine_km(lat, lon, lat0, lon0)
            if d < best_d:
                best = row
                best_d = d
        if best is None or best_d > self.search_radius_km:
            return RiskComponentResult(
                risk_value=0.0,
                confidence=0.0,
                is_missing=True,
                metadata={
                    "source": "weather_obs",
                    "nearest_km": None if best is None else round(best_d, 1),
                },
            )
        wind_norm = max(0.0, min(1.0, float(best.wind_speed) / 25.0))
        wave_norm = max(0.0, min(1.0, float(best.wave_height) / 6.0))
        risk = max(0.0, min(1.0, 0.6 * wind_norm + 0.4 * wave_norm))
        return RiskComponentResult(
            risk_value=risk,
            confidence=0.8,
            is_missing=False,
            metadata={
                "source": "weather_obs",
                "observation_id": str(best.id),
                "wind_speed": best.wind_speed,
                "wave_height": best.wave_height,
                "nearest_km": round(best_d, 1),
            },
        )


class CurrentRiskCalculator(RiskCalculator):
    """Reads ``OceanObservation.current_speed`` and SST."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        search_radius_km: float = 150.0,
    ):
        self.db = db
        self.search_radius_km = search_radius_km

    async def calculate(
        self, lat: float, lon: float, timestamp: Any
    ) -> RiskComponentResult:
        stmt = _nearby_query(OceanObservation, lat, lon)
        rows = (await self.db.execute(stmt)).scalars().all()
        if not rows:
            return RiskComponentResult(
                risk_value=0.0, confidence=0.0, is_missing=True,
                metadata={"source": "ocean_obs"},
            )
        best = None
        best_d = float("inf")
        for row in rows:
            coord = _centroid_or_none(row.geometry)
            if coord is None:
                continue
            lon0, lat0 = coord
            d = haversine_km(lat, lon, lat0, lon0)
            if d < best_d:
                best = row
                best_d = d
        if best is None or best_d > self.search_radius_km:
            return RiskComponentResult(
                risk_value=0.0, confidence=0.0, is_missing=True,
                metadata={"source": "ocean_obs"},
            )
        current_norm = max(0.0, min(1.0, float(best.current_speed) / 2.0))
        sst_anomaly = abs(float(best.sea_surface_temperature))
        sst_norm = max(0.0, min(1.0, sst_anomaly / 5.0))
        risk = max(0.0, min(1.0, 0.8 * current_norm + 0.2 * sst_norm))
        return RiskComponentResult(
            risk_value=risk,
            confidence=0.8,
            is_missing=False,
            metadata={
                "source": "ocean_obs",
                "observation_id": str(best.id),
                "current_speed": best.current_speed,
                "sst": best.sea_surface_temperature,
                "nearest_km": round(best_d, 1),
            },
        )