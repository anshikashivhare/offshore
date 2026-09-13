from typing import List, Optional, Sequence

from app.models.observation import (OceanObservation, SeaIceObservation,
                                    WeatherObservation)
from app.repositories.base import CRUDBase
from app.schemas.observation import (OceanObservationBase,
                                     OceanObservationCreate,
                                     SeaIceObservationBase,
                                     SeaIceObservationCreate,
                                     WeatherObservationBase,
                                     WeatherObservationCreate)
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession


def _bbox_filter(model, min_lat: float, min_lon: float, max_lat: float, max_lon: float):
    """Build a bbox filter that works against GeoAlchemy2 POINT/POLYGON columns.

    Returns None when the geometry column has been monkey-patched to a non-
    spatial type (e.g., during SQLite-based tests). Callers must treat None as
    "no spatial filtering available".
    """
    geom = getattr(model, "geometry", None)
    if geom is None:
        return None
    st_intersects = getattr(geom, "ST_Intersects", None)
    if st_intersects is None:
        return None
    return st_intersects(func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326))


class CRUDSeaIceObservation(
    CRUDBase[SeaIceObservation, SeaIceObservationCreate, SeaIceObservationBase]
):
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        bbox: Optional[Sequence[float]] = None,
        start_time: Optional["object"] = None,
        end_time: Optional["object"] = None,
    ) -> List[SeaIceObservation]:
        stmt = select(SeaIceObservation)
        if bbox and len(bbox) == 4:
            f = _bbox_filter(SeaIceObservation, *bbox)
            if f is not None:
                stmt = stmt.where(f)
        if start_time is not None:
            stmt = stmt.where(SeaIceObservation.timestamp >= start_time)
        if end_time is not None:
            stmt = stmt.where(SeaIceObservation.timestamp <= end_time)
        stmt = (
            stmt.order_by(SeaIceObservation.timestamp.desc()).offset(skip).limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def count(
        self,
        db: AsyncSession,
        *,
        bbox: Optional[Sequence[float]] = None,
        start_time: Optional["object"] = None,
        end_time: Optional["object"] = None,
    ) -> int:
        stmt = select(func.count()).select_from(SeaIceObservation)
        if bbox and len(bbox) == 4:
            f = _bbox_filter(SeaIceObservation, *bbox)
            if f is not None:
                stmt = stmt.where(f)
        if start_time is not None:
            stmt = stmt.where(SeaIceObservation.timestamp >= start_time)
        if end_time is not None:
            stmt = stmt.where(SeaIceObservation.timestamp <= end_time)
        return (await db.execute(stmt)).scalar_one()


class CRUDWeatherObservation(
    CRUDBase[WeatherObservation, WeatherObservationCreate, WeatherObservationBase]
):
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        bbox: Optional[Sequence[float]] = None,
        start_time: Optional["object"] = None,
        end_time: Optional["object"] = None,
    ) -> List[WeatherObservation]:
        stmt = select(WeatherObservation)
        if bbox and len(bbox) == 4:
            f = _bbox_filter(WeatherObservation, *bbox)
            if f is not None:
                stmt = stmt.where(f)
        if start_time is not None:
            stmt = stmt.where(WeatherObservation.timestamp >= start_time)
        if end_time is not None:
            stmt = stmt.where(WeatherObservation.timestamp <= end_time)
        stmt = (
            stmt.order_by(WeatherObservation.timestamp.desc()).offset(skip).limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def count(
        self,
        db: AsyncSession,
        *,
        bbox: Optional[Sequence[float]] = None,
        start_time: Optional["object"] = None,
        end_time: Optional["object"] = None,
    ) -> int:
        stmt = select(func.count()).select_from(WeatherObservation)
        if bbox and len(bbox) == 4:
            f = _bbox_filter(WeatherObservation, *bbox)
            if f is not None:
                stmt = stmt.where(f)
        if start_time is not None:
            stmt = stmt.where(WeatherObservation.timestamp >= start_time)
        if end_time is not None:
            stmt = stmt.where(WeatherObservation.timestamp <= end_time)
        return (await db.execute(stmt)).scalar_one()


class CRUDOceanObservation(
    CRUDBase[OceanObservation, OceanObservationCreate, OceanObservationBase]
):
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        bbox: Optional[Sequence[float]] = None,
        start_time: Optional["object"] = None,
        end_time: Optional["object"] = None,
    ) -> List[OceanObservation]:
        stmt = select(OceanObservation)
        if bbox and len(bbox) == 4:
            f = _bbox_filter(OceanObservation, *bbox)
            if f is not None:
                stmt = stmt.where(f)
        if start_time is not None:
            stmt = stmt.where(OceanObservation.timestamp >= start_time)
        if end_time is not None:
            stmt = stmt.where(OceanObservation.timestamp <= end_time)
        stmt = (
            stmt.order_by(OceanObservation.timestamp.desc()).offset(skip).limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def count(
        self,
        db: AsyncSession,
        *,
        bbox: Optional[Sequence[float]] = None,
        start_time: Optional["object"] = None,
        end_time: Optional["object"] = None,
    ) -> int:
        stmt = select(func.count()).select_from(OceanObservation)
        if bbox and len(bbox) == 4:
            f = _bbox_filter(OceanObservation, *bbox)
            if f is not None:
                stmt = stmt.where(f)
        if start_time is not None:
            stmt = stmt.where(OceanObservation.timestamp >= start_time)
        if end_time is not None:
            stmt = stmt.where(OceanObservation.timestamp <= end_time)
        return (await db.execute(stmt)).scalar_one()


sea_ice_observation = CRUDSeaIceObservation(SeaIceObservation)
weather_observation = CRUDWeatherObservation(WeatherObservation)
ocean_observation = CRUDOceanObservation(OceanObservation)
