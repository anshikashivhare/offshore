from typing import Any, List, Optional, Sequence

from app.models.iceberg import (Iceberg, IcebergDetection,
                                IcebergTrajectoryPrediction)
from app.repositories.base import CRUDBase
from app.schemas.iceberg import (IcebergDetectionBase, IcebergDetectionCreate,
                                 IcebergTrajectoryPredictionBase,
                                 IcebergTrajectoryPredictionCreate)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDIceberg(CRUDBase[Iceberg, Any, Any]):
    async def get(self, db: AsyncSession, id: Any) -> Optional[Iceberg]:
        result = await db.execute(select(Iceberg).filter(Iceberg.iceberg_id == id))
        return result.scalars().first()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Iceberg]:
        stmt = select(Iceberg).order_by(Iceberg.iceberg_id).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def count(self, db: AsyncSession) -> int:
        return (
            await db.execute(select(func.count()).select_from(Iceberg))
        ).scalar_one()

    async def create(self, db: AsyncSession, *, obj_in: Any = None) -> Iceberg:
        obj = Iceberg()
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def get_or_create(self, db: AsyncSession, *, iceberg_id: Any) -> Iceberg:
        existing = await self.get(db, iceberg_id)
        if existing is not None:
            return existing
        obj = Iceberg(iceberg_id=iceberg_id)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj


class CRUDIcebergDetection(
    CRUDBase[IcebergDetection, IcebergDetectionCreate, IcebergDetectionBase]
):
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        iceberg_id: Optional[Any] = None,
        bbox: Optional[Sequence[float]] = None,
    ) -> List[IcebergDetection]:
        stmt = select(IcebergDetection)
        if iceberg_id is not None:
            stmt = stmt.where(IcebergDetection.iceberg_id == iceberg_id)
        if bbox and len(bbox) == 4:
            st_intersects = getattr(IcebergDetection.geometry, "ST_Intersects", None)
            if st_intersects is not None:
                stmt = stmt.where(
                    st_intersects(
                        func.ST_MakeEnvelope(bbox[1], bbox[0], bbox[3], bbox[2], 4326)
                    )
                )
        stmt = (
            stmt.order_by(IcebergDetection.timestamp.desc()).offset(skip).limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def count(
        self,
        db: AsyncSession,
        *,
        iceberg_id: Optional[Any] = None,
    ) -> int:
        stmt = select(func.count()).select_from(IcebergDetection)
        if iceberg_id is not None:
            stmt = stmt.where(IcebergDetection.iceberg_id == iceberg_id)
        return (await db.execute(stmt)).scalar_one()

    async def latest_for_iceberg(
        self, db: AsyncSession, iceberg_id: Any
    ) -> Optional[IcebergDetection]:
        stmt = (
            select(IcebergDetection)
            .where(IcebergDetection.iceberg_id == iceberg_id)
            .order_by(IcebergDetection.timestamp.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalars().first()


class CRUDIcebergTrajectoryPrediction(
    CRUDBase[
        IcebergTrajectoryPrediction,
        IcebergTrajectoryPredictionCreate,
        IcebergTrajectoryPredictionBase,
    ]
):
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        iceberg_id: Optional[Any] = None,
    ) -> List[IcebergTrajectoryPrediction]:
        stmt = select(IcebergTrajectoryPrediction)
        if iceberg_id is not None:
            stmt = stmt.where(IcebergTrajectoryPrediction.iceberg_id == iceberg_id)
        stmt = (
            stmt.order_by(IcebergTrajectoryPrediction.prediction_timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()


iceberg = CRUDIceberg(Iceberg)
iceberg_detection = CRUDIcebergDetection(IcebergDetection)
iceberg_prediction = CRUDIcebergTrajectoryPrediction(IcebergTrajectoryPrediction)
