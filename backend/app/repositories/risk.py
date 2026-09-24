from typing import Any, List, Optional, Sequence

from app.models.risk import RiskCell
from app.repositories.base import CRUDBase
from app.schemas.risk import RiskCellBase, RiskCellCreate
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDRiskCell(CRUDBase[RiskCell, RiskCellCreate, RiskCellBase]):
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        bbox: Optional[Sequence[float]] = None,
        start_time: Optional["object"] = None,
        end_time: Optional["object"] = None,
    ) -> List[RiskCell]:
        stmt = select(RiskCell)
        if bbox and len(bbox) == 4:
            st_intersects = getattr(RiskCell.geometry, "ST_Intersects", None)
            if st_intersects is not None:
                stmt = stmt.where(
                    st_intersects(
                        func.ST_MakeEnvelope(bbox[1], bbox[0], bbox[3], bbox[2], 4326)
                    )
                )
        if start_time is not None:
            stmt = stmt.where(RiskCell.timestamp >= start_time)
        if end_time is not None:
            stmt = stmt.where(RiskCell.timestamp <= end_time)
        stmt = stmt.order_by(RiskCell.timestamp.desc()).offset(skip).limit(limit)
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
        stmt = select(func.count()).select_from(RiskCell)
        if bbox and len(bbox) == 4:
            st_intersects = getattr(RiskCell.geometry, "ST_Intersects", None)
            if st_intersects is not None:
                stmt = stmt.where(
                    st_intersects(
                        func.ST_MakeEnvelope(bbox[1], bbox[0], bbox[3], bbox[2], 4326)
                    )
                )
        if start_time is not None:
            stmt = stmt.where(RiskCell.timestamp >= start_time)
        if end_time is not None:
            stmt = stmt.where(RiskCell.timestamp <= end_time)
        return (await db.execute(stmt)).scalar_one()

    async def bulk_upsert_forecasts(self, db: AsyncSession, cells_data: List[dict]) -> None:
        from sqlalchemy.dialects.postgresql import insert
        
        if not cells_data:
            return

        stmt = insert(RiskCell).values(cells_data)
        
        # ON CONFLICT UPDATE
        update_dict = {
            c.name: c
            for c in stmt.excluded
            if c.name not in ["id", "geometry", "timestamp"]
        }
        
        stmt = stmt.on_conflict_do_update(
            constraint="uix_risk_cell_geom_time",
            set_=update_dict
        )
        
        await db.execute(stmt)
        await db.commit()

risk_cell = CRUDRiskCell(RiskCell)
