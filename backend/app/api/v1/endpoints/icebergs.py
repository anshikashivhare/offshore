import asyncio as _aio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from app.api import deps
from app.repositories.iceberg import iceberg as iceberg_repo
from app.repositories.iceberg import iceberg_detection as detection_repo
from app.schemas.common import GeoJSONFeatureCollection
from app.schemas.iceberg import (IcebergDetectionProperties, IcebergResponse,
                                 IcebergTrajectoryPredictionProperties)
from app.services.icebergs.detection import DeterministicSeededDetector
from app.services.icebergs.tracking import IcebergTracker
from app.services.icebergs.trajectory import PhysicsBasedTrajectoryPredictor
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _detector(db: AsyncSession) -> DeterministicSeededDetector:
    return DeterministicSeededDetector(db)


def _tracker(db: AsyncSession) -> IcebergTracker:
    return IcebergTracker(db)


def _trajectory(db: AsyncSession) -> PhysicsBasedTrajectoryPredictor:
    return PhysicsBasedTrajectoryPredictor(db)


@router.get(
    "/detections",
    response_model=GeoJSONFeatureCollection[IcebergDetectionProperties],
)
async def get_iceberg_detections(
    db: AsyncSession = Depends(deps.get_db),
    pagination: deps.PaginationParams = Depends(),
    time_range: deps.TimeRangeParams = Depends(),
    bbox: deps.BBoxParams = Depends(),
) -> Any:
    """Run iceberg detection within the requested bbox.

    Persists the generated detections to the database so that subsequent calls
    to ``/{id}/track`` and ``/{id}/trajectory`` return stable data.
    """
    bb: Dict[str, float] = {
        "min_lon": bbox.min_lon if bbox.min_lon is not None else 0.0,
        "min_lat": bbox.min_lat if bbox.min_lat is not None else 0.0,
        "max_lon": bbox.max_lon if bbox.max_lon is not None else 0.0,
        "max_lat": bbox.max_lat if bbox.max_lat is not None else 0.0,
    }
    now = datetime.now(timezone.utc)
    features = await _detector(db).detect(
        f"bbox:{bb['min_lon']},{bb['min_lat']},{bb['max_lon']},{bb['max_lat']}:{now.isoformat()}",
        now,
        bb,
    )
    return GeoJSONFeatureCollection[IcebergDetectionProperties].from_list(
        items=features,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/{iceberg_id}", response_model=IcebergResponse)
async def get_iceberg(
    iceberg_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """Return iceberg metadata (id + latest known detection summary)."""
    iceberg = await iceberg_repo.get(db, iceberg_id)
    if iceberg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Iceberg not found"
        )
    # FIX: run latest detection + count concurrently instead of 2 sequential awaits.
    latest, n_detections = await _aio.gather(
        detection_repo.latest_for_iceberg(db, iceberg_id),
        detection_repo.count(db, iceberg_id=iceberg_id),
    )
    return IcebergResponse(
        iceberg_id=iceberg.iceberg_id,
        latest_detection_id=latest.id if latest else None,
        latest_detection_timestamp=latest.timestamp if latest else None,
        n_detections=n_detections,
    )


@router.get(
    "/{iceberg_id}/track",
    response_model=GeoJSONFeatureCollection[IcebergDetectionProperties],
)
async def get_iceberg_track(
    iceberg_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    pagination: deps.PaginationParams = Depends(),
    time_range: deps.TimeRangeParams = Depends(),
) -> Any:
    """Return the historical detection track for an iceberg."""
    iceberg = await iceberg_repo.get(db, iceberg_id)
    if iceberg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Iceberg not found"
        )
    features = await _tracker(db).build_track(iceberg_id)
    return GeoJSONFeatureCollection[IcebergDetectionProperties].from_list(
        items=features,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/{iceberg_id}/trajectory",
    response_model=GeoJSONFeatureCollection[IcebergTrajectoryPredictionProperties],
)
async def get_iceberg_trajectory(
    iceberg_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
    horizon_hours: int = 24,
) -> Any:
    """Predict the future trajectory for an iceberg using physics-based advection."""
    iceberg = await iceberg_repo.get(db, iceberg_id)
    if iceberg is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Iceberg not found"
        )
    if horizon_hours < 1 or horizon_hours > 168:
        raise HTTPException(
            status_code=422, detail="horizon_hours must be between 1 and 168 (7 days)."
        )
    historical_track = await _tracker(db).build_track(iceberg_id)
    predictions = await _trajectory(db).predict_trajectory(
        iceberg_id=iceberg_id,
        historical_track=historical_track,
        environmental_conditions={},
        horizon_hours=horizon_hours,
        start_time=datetime.now(timezone.utc),
    )
    return GeoJSONFeatureCollection[IcebergTrajectoryPredictionProperties].from_list(
        items=predictions,
        skip=0,
        limit=len(predictions),
    )
