from typing import Any, Optional

from app.models.vessel import Vessel
from app.repositories.base import CRUDBase
from app.schemas.vessel import VesselBase, VesselCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDVessel(CRUDBase[Vessel, VesselCreate, VesselBase]):
    async def get_by_name(
        self, db: AsyncSession, *, vessel_name: str
    ) -> Optional[Vessel]:
        result = await db.execute(
            select(Vessel).filter(Vessel.vessel_name == vessel_name)
        )
        return result.scalars().first()

    # Override get since pk is vessel_id
    async def get(self, db: AsyncSession, id: Any) -> Optional[Vessel]:
        result = await db.execute(select(Vessel).filter(Vessel.vessel_id == id))
        return result.scalars().first()


    async def get_filtered(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, name: Optional[str] = None, country: Optional[str] = None
    ) -> list[Vessel]:
        stmt = select(Vessel)
        if name:
            stmt = stmt.where(Vessel.vessel_name.ilike(f"%{name}%"))
        if country:
            stmt = stmt.where(Vessel.flag_country.ilike(f"%{country}%"))
        stmt = stmt.offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
        
    async def count_filtered(
        self, db: AsyncSession, *, name: Optional[str] = None, country: Optional[str] = None
    ) -> int:
        from sqlalchemy import func
        stmt = select(func.count(Vessel.vessel_id))
        if name:
            stmt = stmt.where(Vessel.vessel_name.ilike(f"%{name}%"))
        if country:
            stmt = stmt.where(Vessel.flag_country.ilike(f"%{country}%"))
        result = await db.execute(stmt)
        return result.scalar_one()

vessel = CRUDVessel(Vessel)
