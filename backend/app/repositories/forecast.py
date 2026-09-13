from typing import Any, List, Optional

from app.models.forecast import Forecast
from app.repositories.base import CRUDBase
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDForecast(CRUDBase[Forecast, Any, Any]):
    async def get(self, db: AsyncSession, id: Any) -> Optional[Forecast]:
        result = await db.execute(select(Forecast).filter(Forecast.id == id))
        return result.scalars().first()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Forecast]:
        stmt = (
            select(Forecast)
            .order_by(Forecast.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, obj_in: Any) -> Forecast:
        data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump()
        obj = Forecast(**data)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj


forecast = CRUDForecast(Forecast)
