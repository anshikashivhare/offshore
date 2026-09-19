from datetime import datetime, timezone
from typing import AsyncGenerator, List, Optional

from app.db.session import AsyncSessionLocal
from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp into a tz-aware UTC datetime.

    Accepts trailing 'Z' as UTC. Returns None for falsy input. Raises ValueError
    on malformed strings so the API returns a 422 with a clear message.
    """
    if not value:
        return None
    s = value.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class PaginationParams:
    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Skip the first N records"),
        limit: int = Query(
            100, ge=1, le=6000, description="Limit the number of records returned"
        ),
    ):
        self.skip = skip
        self.limit = limit


class TimeRangeParams:
    def __init__(
        self,
        start_time: Optional[str] = Query(
            None, description="Start timestamp (ISO 8601, e.g. 2026-09-03T00:00:00Z)"
        ),
        end_time: Optional[str] = Query(
            None, description="End timestamp (ISO 8601, e.g. 2026-09-03T23:59:59Z)"
        ),
    ):
        self.start_time = _parse_iso(start_time)
        self.end_time = _parse_iso(end_time)


class BBoxParams:
    """Bounding-box dependency. All four values must be provided together."""

    def __init__(
        self,
        min_lat: Optional[float] = Query(
            None, ge=-90, le=90, description="Minimum latitude"
        ),
        min_lon: Optional[float] = Query(
            None, ge=-180, le=180, description="Minimum longitude"
        ),
        max_lat: Optional[float] = Query(
            None, ge=-90, le=90, description="Maximum latitude"
        ),
        max_lon: Optional[float] = Query(
            None, ge=-180, le=180, description="Maximum longitude"
        ),
    ):
        self.min_lat = min_lat
        self.min_lon = min_lon
        self.max_lat = max_lat
        self.max_lon = max_lon

    def as_tuple(self) -> Optional[List[float]]:
        if None in (self.min_lat, self.min_lon, self.max_lat, self.max_lon):
            return None
        if self.min_lat > self.max_lat or self.min_lon > self.max_lon:
            raise ValueError(
                "Invalid bounding box: min_lat must be <= max_lat and "
                "min_lon must be <= max_lon."
            )
        return [self.min_lat, self.min_lon, self.max_lat, self.max_lon]
