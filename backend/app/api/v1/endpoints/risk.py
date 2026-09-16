import asyncio as _aio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.api import deps
from app.models.risk import RiskCell
from app.repositories.risk import risk_cell as risk_cell_repo
from app.schemas.common import GeoJSONFeature, GeoJSONFeatureCollection
from app.schemas.risk import RiskCellProperties, RiskCellResponse
from app.services.risk.engine import DEFAULT_WEIGHTS, RiskEngine
from app.utils.geojson import to_geojson_geometry
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class GenerateMapRequest(BaseModel):
    bbox: str = Field(
        "-180,-90,180,90",
        description="Bounding box as 'minx,miny,maxx,maxy' in EPSG:4326.",
    )
    timestamp: Optional[datetime] = None
    weights: Optional[Dict[str, float]] = None
    resolution_deg: float = Field(
        1.0, ge=0.05, le=10.0, description="Grid resolution in degrees."
    )


def _parse_bbox(bbox: str) -> List[float]:
    try:
        parts = [float(x) for x in bbox.split(",")]
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"bbox must be 'minx,miny,maxx,maxy' (got {bbox!r}).",
        ) from exc
    if len(parts) != 4:
        raise HTTPException(
            status_code=422,
            detail="bbox must contain exactly 4 comma-separated floats.",
        )
    minx, miny, maxx, maxy = parts
    if not (-180.0 <= minx <= 180.0 and -180.0 <= maxx <= 180.0):
        raise HTTPException(status_code=422, detail="longitude values out of range.")
    if not (-90.0 <= miny <= 90.0 and -90.0 <= maxy <= 90.0):
        raise HTTPException(status_code=422, detail="latitude values out of range.")
    if minx >= maxx or miny >= maxy:
        raise HTTPException(
            status_code=422,
            detail="bbox must satisfy minx < maxx and miny < maxy.",
        )
    return [minx, miny, maxx, maxy]


async def _get_cells_with_total(
    db: AsyncSession,
    *,
    skip: int,
    limit: int,
    bb: Optional[List[float]],
    time_range: deps.TimeRangeParams,
):
    """Run get_multi and count concurrently to halve DB round-trips."""
    cells, total = await _aio.gather(
        risk_cell_repo.get_multi(
            db,
            skip=skip,
            limit=limit,
            bbox=bb,
            start_time=time_range.start_time,
            end_time=time_range.end_time,
        ),
        risk_cell_repo.count(
            db,
            bbox=bb,
            start_time=time_range.start_time,
            end_time=time_range.end_time,
        ),
    )
    return cells, total


@router.post("/map", status_code=status.HTTP_201_CREATED)
async def generate_risk_map(
    request: GenerateMapRequest,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """Generate a grid of risk cells for the given bbox and persist them."""
    minx, miny, maxx, maxy = _parse_bbox(request.bbox)
    timestamp = request.timestamp or datetime.now(timezone.utc)
    weights = request.weights or dict(DEFAULT_WEIGHTS)

    engine = RiskEngine(db=db)
    try:
        cells = await engine.calculate_grid_risk(
            min_lat=miny,
            min_lon=minx,
            max_lat=maxy,
            max_lon=maxx,
            resolution_deg=request.resolution_deg,
            timestamp=timestamp,
            weights=weights,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if not cells:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Grid produced no cells. Check bbox and resolution.",
        )

    # FIX: bulk insert all cells in a single commit instead of flushing per row.
    db_cells = [RiskCell(**cell_data.model_dump()) for cell_data in cells]
    db.add_all(db_cells)
    await db.commit()
    for db_cell in db_cells:
        await db.refresh(db_cell)

    return {
        "message": "Risk map generated",
        "cell_ids": [str(c.id) for c in db_cells],
        "n_cells": len(db_cells),
    }


@router.get("/map")
async def get_risk_map(
    db: AsyncSession = Depends(deps.get_db),
    pagination: deps.PaginationParams = Depends(),
    time_range: deps.TimeRangeParams = Depends(),
    bbox: deps.BBoxParams = Depends(),
) -> Any:
    """Get the most recent risk cells for a bbox/time range (paginated).

    Returns a GeoJSON FeatureCollection. For a continuous raster surface, build
    it client-side from the returned cells.
    """
    # FIX: replaced hardcoded limit=1000 with PaginationParams.
    bb: Optional[List[float]] = None
    try:
        bb = bbox.as_tuple()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    cells, total = await _get_cells_with_total(
        db, skip=pagination.skip, limit=pagination.limit, bb=bb, time_range=time_range
    )
    features = [
        GeoJSONFeature[RiskCellResponse](
            geometry=to_geojson_geometry(cell.geometry),
            properties=RiskCellProperties.model_validate(cell),
        )
        for cell in cells
    ]
    return GeoJSONFeatureCollection[RiskCellResponse](
        features=features,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get("/cells", response_model=GeoJSONFeatureCollection[RiskCellProperties])
async def get_risk_cells(
    db: AsyncSession = Depends(deps.get_db),
    pagination: deps.PaginationParams = Depends(),
    time_range: deps.TimeRangeParams = Depends(),
    bbox: deps.BBoxParams = Depends(),
) -> Any:
    """List discrete risk cells with bbox/time/pagination filters."""
    bb: Optional[List[float]] = None
    try:
        bb = bbox.as_tuple()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    cells, total = await _get_cells_with_total(
        db, skip=pagination.skip, limit=pagination.limit, bb=bb, time_range=time_range
    )
    features = [
        GeoJSONFeature[RiskCellResponse](
            geometry=to_geojson_geometry(cell.geometry),
            properties=RiskCellProperties.model_validate(cell),
        )
        for cell in cells
    ]
    return GeoJSONFeatureCollection[RiskCellResponse](
        features=features,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit,
    )
