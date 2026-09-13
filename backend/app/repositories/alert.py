from typing import Any, List, Optional, Sequence

from app.models.alert import Alert
from app.repositories.base import CRUDBase
from app.schemas.alert import AlertBase, AlertCreate
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDAlert(CRUDBase[Alert, AlertCreate, AlertBase]):
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        route_id: Optional[Any] = None,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
        start_time: Optional["object"] = None,
        end_time: Optional["object"] = None,
    ) -> List[Alert]:
        stmt = select(Alert)
        if route_id is not None:
            stmt = stmt.where(Alert.route_id == route_id)
        if severity is not None:
            stmt = stmt.where(Alert.severity == severity)
        if alert_type is not None:
            stmt = stmt.where(Alert.alert_type == alert_type)
        if start_time is not None:
            stmt = stmt.where(Alert.timestamp >= start_time)
        if end_time is not None:
            stmt = stmt.where(Alert.timestamp <= end_time)
        stmt = stmt.order_by(Alert.timestamp.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def count(
        self,
        db: AsyncSession,
        *,
        route_id: Optional[Any] = None,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
        start_time: Optional["object"] = None,
        end_time: Optional["object"] = None,
    ) -> int:
        stmt = select(func.count()).select_from(Alert)
        if route_id is not None:
            stmt = stmt.where(Alert.route_id == route_id)
        if severity is not None:
            stmt = stmt.where(Alert.severity == severity)
        if alert_type is not None:
            stmt = stmt.where(Alert.alert_type == alert_type)
        if start_time is not None:
            stmt = stmt.where(Alert.timestamp >= start_time)
        if end_time is not None:
            stmt = stmt.where(Alert.timestamp <= end_time)
        return (await db.execute(stmt)).scalar_one()


alert = CRUDAlert(Alert)
