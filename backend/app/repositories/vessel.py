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


vessel = CRUDVessel(Vessel)
