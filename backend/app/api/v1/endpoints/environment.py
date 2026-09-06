from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.repositories.observation import (
    ocean_observation,
    sea_ice_observation,
    weather_observation,
)
from app.schemas.common import GeoJSONFeature, GeoJSONFeatureCollection
from app.schemas.observation import (
    OceanObservationProperties,
    OceanObservationResponse,
    SeaIceObservationProperties,
    SeaIceObservationResponse,
    WeatherObservationProperties,
    WeatherObservationResponse,
)
from app.utils.geojson import to_geojson_geometry

router = APIRouter()


def _bbox_or_400(bbox: deps.BBoxParams) -> List[float]:
    try:
        bb = bbox.as_tuple()
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    if bb is None:
        raise HTTPException(
            status_code=422,
            detail="All four bbox parameters (min_lat, min_lon, max_lat, max_lon) are required.",
        )
    return bb


@router.get(
    "/sea-ice",
    response_model=GeoJSONFeatureCollection[SeaIceObservationResponse],
)
async def get_sea_ice_observations(
    db: AsyncSession = Depends(deps.get_db),
    pagination: deps.PaginationParams = Depends(),
    time_range: deps.TimeRangeParams = Depends(),
    bbox: deps.BBoxParams = Depends(),
) -> Any:
    """Retrieve sea-ice observations filtered by bbox and time range."""
    bb = _bbox_or_400(bbox)
    rows = await sea_ice_observation.get_multi(
        db,
        skip=pagination.skip,
        limit=pagination.limit,
        bbox=bb,
        start_time=time_range.start_time,
        end_time=time_range.end_time,
    )
    features = [
        GeoJSONFeature[SeaIceObservationResponse](
            geometry=to_geojson_geometry(r.geometry),
            properties=SeaIceObservationProperties.model_validate(r),
        )
        for r in rows
    ]
    return GeoJSONFeatureCollection[SeaIceObservationResponse](
        features=features,
        total=len(features),
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/weather",
    response_model=GeoJSONFeatureCollection[WeatherObservationResponse],
)
async def get_weather_observations(
    db: AsyncSession = Depends(deps.get_db),
    pagination: deps.PaginationParams = Depends(),
    time_range: deps.TimeRangeParams = Depends(),
    bbox: deps.BBoxParams = Depends(),
) -> Any:
    """Retrieve weather observations filtered by bbox and time range."""
    bb = _bbox_or_400(bbox)
    rows = await weather_observation.get_multi(
        db,
        skip=pagination.skip,
        limit=pagination.limit,
        bbox=bb,
        start_time=time_range.start_time,
        end_time=time_range.end_time,
    )
    features = [
        GeoJSONFeature[WeatherObservationResponse](
            geometry=to_geojson_geometry(r.geometry),
            properties=WeatherObservationProperties.model_validate(r),
        )
        for r in rows
    ]
    return GeoJSONFeatureCollection[WeatherObservationResponse](
        features=features,
        total=len(features),
        skip=pagination.skip,
        limit=pagination.limit,
    )


@router.get(
    "/ocean",
    response_model=GeoJSONFeatureCollection[OceanObservationResponse],
)
async def get_ocean_observations(
    db: AsyncSession = Depends(deps.get_db),
    pagination: deps.PaginationParams = Depends(),
    time_range: deps.TimeRangeParams = Depends(),
    bbox: deps.BBoxParams = Depends(),
) -> Any:
    """Retrieve ocean-current observations filtered by bbox and time range."""
    bb = _bbox_or_400(bbox)
    rows = await ocean_observation.get_multi(
        db,
        skip=pagination.skip,
        limit=pagination.limit,
        bbox=bb,
        start_time=time_range.start_time,
        end_time=time_range.end_time,
    )
    features = [
        GeoJSONFeature[OceanObservationResponse](
            geometry=to_geojson_geometry(r.geometry),
            properties=OceanObservationProperties.model_validate(r),
        )
        for r in rows
    ]
    return GeoJSONFeatureCollection[OceanObservationResponse](
        features=features,
        total=len(features),
        skip=pagination.skip,
        limit=pagination.limit,
    )