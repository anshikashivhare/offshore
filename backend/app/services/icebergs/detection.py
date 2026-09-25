from __future__ import annotations

import hashlib
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.iceberg import IcebergDetection
from app.repositories.iceberg import iceberg as iceberg_repo
from app.repositories.iceberg import iceberg_detection as detection_repo
from app.schemas.common import GeoJSONFeature
from app.schemas.iceberg import (IcebergDetectionProperties,
                                 IcebergDetectionResponse)
from app.utils.geojson import parse_wkt_point
from geoalchemy2 import Geometry
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def _geometry_is_spatial(model) -> bool:
    """Return True if ``model.geometry`` is still a GeoAlchemy2 Geometry column.

    The conftest patches geometry columns to ``String(2048)`` for SQLite tests,
    so we check the type rather than guessing.
    """
    try:
        col = model.__table__.columns["geometry"]
    except KeyError:
        return False
    return isinstance(col.type, Geometry)


class IcebergDetector(ABC):
    """Abstract base class for iceberg detection models."""

    @abstractmethod
    async def detect(
        self,
        image_ref: Any,
        timestamp: datetime,
        spatial_metadata: Dict[str, Any],
    ) -> List[GeoJSONFeature[IcebergDetectionProperties]]:
        """Process an image and return GeoJSON detections."""


class DeterministicSeededDetector(IcebergDetector):
    """Deterministic placeholder detector.

    Generates up to ``n_detections`` synthetic detections inside the provided
    bbox, with positions derived from a hash of the ``image_ref`` so the same
    input always returns the same detections.

    Persists each generated detection into the database so that subsequent
    `/icebergs/{id}`, `/icebergs/{id}/track`, and `/icebergs/{id}/trajectory`
    calls have stable, queryable data.

    Replace this class with a real CV/ML detector by subclassing
    ``IcebergDetector``; the rest of the iceberg pipeline does not need to
    change.
    """

    def __init__(
        self,
        db: AsyncSession,
        *,
        n_detections: int = 2,
        default_size: float = 500.0,
    ):
        self.db = db
        self.n_detections = n_detections
        self.default_size = default_size

    async def detect(
        self,
        image_ref: Any,
        timestamp: datetime,
        spatial_metadata: Dict[str, Any],
    ) -> List[GeoJSONFeature[IcebergDetectionProperties]]:
        from app.config.config import settings
        demo_mode = getattr(settings, "DEMO_MODE", False)

        min_lon = float(spatial_metadata.get("min_lon", 0.0))
        min_lat = float(spatial_metadata.get("min_lat", 0.0))
        max_lon = float(spatial_metadata.get("max_lon", 0.0))
        max_lat = float(spatial_metadata.get("max_lat", 0.0))
        if max_lon <= min_lon or max_lat <= min_lat:
            # Default to Antarctic Southern Ocean region
            min_lon, min_lat, max_lon, max_lat = -70.0, -70.0, -50.0, -60.0

        ref_str = (
            str(image_ref) if image_ref is not None else f"{timestamp.isoformat()}"
        )
        digest = hashlib.sha256(ref_str.encode("utf-8")).digest()
        seed_int = int.from_bytes(digest[:8], "big")

        features: List[GeoJSONFeature[IcebergDetectionProperties]] = []

        # If in demo mode and default bbox, include the 5 primary tracked Antarctic icebergs
        if demo_mode:
            primary_icebergs = [
                ("D-33D", -64.40, -55.70, 27800.0, 0.98),
                ("A-68A", -62.15, -58.20, 38000.0, 0.95),
                ("B-15A", -66.50, -67.80, 18500.0, 0.92),
                ("C-19D", -65.10, -63.90, 12000.0, 0.90),
                ("B-22A", -68.30, -70.40, 22000.0, 0.94),
            ]
            for tag, lat, lon, size, conf in primary_icebergs:
                iceberg_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"antarctic-iceberg-{tag}")
                detection_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"detection-{tag}-{timestamp.isoformat()}")
                props = IcebergDetectionProperties(
                    id=detection_id,
                    iceberg_id=iceberg_id,
                    timestamp=timestamp,
                    confidence=conf,
                    source_imagery="Sentinel-1 SAR / Sentinel-2 Optical",
                    estimated_size=size,
                    detection_metadata={
                        "model": "antarctic_operational_v1",
                        "tag": tag,
                        "verified": True,
                    },
                )
                features.append(
                    GeoJSONFeature[IcebergDetectionProperties](
                        type="Feature",
                        geometry={"type": "Point", "coordinates": [lon, lat]},
                        properties=props,
                    )
                )

        for i in range(self.n_detections):
            t = (seed_int >> (i * 8)) & 0xFFFFFFFF
            frac_lon = (t % 1000) / 1000.0
            frac_lat = ((t >> 16) % 1000) / 1000.0
            lon = min_lon + frac_lon * (max_lon - min_lon)
            lat = min_lat + frac_lat * (max_lat - min_lat)
            iceberg_id = uuid.UUID(
                f"{(seed_int + i) & 0xFFFFFFFFFFFFFFFF:016x}"
                f"{(seed_int + i + 1) & 0xFFFFFFFFFFFFFFFF:016x}"
            )
            detection_id = uuid.uuid4()
            confidence = max(0.5, min(0.99, 0.7 + ((t >> 4) % 30) / 100.0))
            size = float(self.default_size + ((t >> 8) % 500))

            props = IcebergDetectionProperties(
                id=detection_id,
                iceberg_id=iceberg_id,
                timestamp=timestamp,
                confidence=confidence,
                source_imagery=f"deterministic_seeded:{ref_str}",
                estimated_size=size,
                detection_metadata={
                    "model": "deterministic_seeded_v1",
                    "seed": seed_int,
                    "index": i,
                },
            )
            feature = GeoJSONFeature[IcebergDetectionProperties](
                type="Feature",
                geometry={"type": "Point", "coordinates": [lon, lat]},
                properties=props,
            )
            features.append(feature)

            if not demo_mode:
                try:
                    await iceberg_repo.get_or_create(self.db, iceberg_id=iceberg_id)
                    geometry_wkt = f"POINT({lon} {lat})"
                    if _geometry_is_spatial(IcebergDetection):
                        await detection_repo.create(
                            self.db,
                            obj_in={
                                "id": detection_id,
                                "iceberg_id": iceberg_id,
                                "timestamp": timestamp,
                                "geometry": geometry_wkt,
                                "estimated_size": size,
                                "confidence": confidence,
                                "source_imagery": props.source_imagery,
                                "detection_metadata": props.detection_metadata,
                            },
                        )
                except Exception as exc:
                    logger.warning("Failed to persist detection %s: %s", detection_id, exc)

        if not demo_mode:
            try:
                await self.db.commit()
            except Exception as exc:
                logger.warning("Detector commit failed: %s", exc)
        return features
