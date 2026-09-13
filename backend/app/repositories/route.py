from typing import Any, Optional

from app.models.route import Route
from app.repositories.base import CRUDBase
from app.schemas.route import RouteBase, RouteCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDRoute(CRUDBase[Route, RouteCreate, RouteBase]):
    async def get(self, db: AsyncSession, id: Any) -> Optional[Route]:
        result = await db.execute(select(Route).filter(Route.route_id == id))
        return result.scalars().first()


route = CRUDRoute(Route)
