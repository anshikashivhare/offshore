from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base import CRUDBase
from app.models.route import Route
from app.schemas.route import RouteCreate, RouteBase

class CRUDRoute(CRUDBase[Route, RouteCreate, RouteBase]):
    async def get(self, db: AsyncSession, id: Any) -> Optional[Route]:
        result = await db.execute(select(Route).filter(Route.route_id == id))
        return result.scalars().first()

route = CRUDRoute(Route)
