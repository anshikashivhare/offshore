from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from app.models.iceberg import IcebergDetection
from app.repositories.iceberg import iceberg_detection as detection_repo
from app.schemas.common import GeoJSONFeature
from app.schemas.iceberg import IcebergDetectionProperties
from app.utils.geojson import to_geojson_geometry
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class IcebergTracker:
    """Persists and retrieves iceberg detection tracks.

    The tracker no longer maintains any in-memory state. It reads detection
    rows from the database and returns them as GeoJSON features ordered by
    timestamp. ``associate`` is a no-op for persisted detections; new
    detections are written by the detector.
    """

    def __init__(
        self, db: AsyncSession, association_strategy: str = "nearest_neighbor"
    ):
        self.db = db
        self.association_strategy = association_strategy

    async def associate(
        self, detections: List[GeoJSONFeature[IcebergDetectionProperties]]
    ) -> None:
        """No-op for persisted detections; kept for backwards compatibility."""
        return None

    async def build_track(
        self, iceberg_id: uuid.UUID
    ) -> List[GeoJSONFeature[IcebergDetectionProperties]]:
        rows: List[IcebergDetection] = await detection_repo.get_multi(
            self.db, iceberg_id=iceberg_id, limit=1000
        )
        rows.sort(key=lambda r: r.timestamp)
        features: List[GeoJSONFeature[IcebergDetectionProperties]] = []
        for r in rows:
            properties = IcebergDetectionProperties(
                id=r.id,
                iceberg_id=r.iceberg_id,
                timestamp=r.timestamp,
                confidence=r.confidence,
                source_imagery=r.source_imagery,
                estimated_size=r.estimated_size,
                detection_metadata=r.detection_metadata or {},
            )
            features.append(
                GeoJSONFeature[IcebergDetectionProperties](
                    type="Feature",
                    geometry=to_geojson_geometry(r.geometry),
                    properties=properties,
                )
            )
        return features

    async def gap_report(self, iceberg_id: uuid.UUID) -> List[dict]:
        """Return observation gaps for a given iceberg (sorted by start time)."""
        rows = await detection_repo.get_multi(
            self.db, iceberg_id=iceberg_id, limit=1000
        )
        rows.sort(key=lambda r: r.timestamp)
        gaps: List[dict] = []
        for prev, curr in zip(rows, rows[1:]):
            delta = (curr.timestamp - prev.timestamp).total_seconds()
            if delta > 6 * 3600:  # flag gaps > 6 hours
                gaps.append(
                    {
                        "from": prev.timestamp.isoformat(),
                        "to": curr.timestamp.isoformat(),
                        "duration_hours": round(delta / 3600.0, 2),
                    }
                )
        return gaps
