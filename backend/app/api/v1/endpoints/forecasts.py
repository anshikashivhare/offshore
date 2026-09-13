import uuid
from datetime import datetime
from typing import Any

from app.api import deps
from app.repositories.forecast import forecast as forecast_repo
from app.schemas.forecast import ForecastRequest, ForecastResult
from app.services.forecasting.base import SeaIceForecaster
from app.services.forecasting.baseline import BaselinePersistenceForecaster
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def get_forecaster(db: AsyncSession = None) -> SeaIceForecaster:
    return BaselinePersistenceForecaster(db=db)


@router.post(
    "/sea-ice",
    response_model=ForecastResult,
    status_code=status.HTTP_201_CREATED,
)
async def generate_sea_ice_forecast(
    request: ForecastRequest,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """Generate a sea-ice forecast and persist the result."""
    forecaster = get_forecaster(db=db)
    try:
        forecaster.validate_input(request)
        result = await forecaster.predict(
            inputs=request,
            horizon=request.horizon_days,
            region=request.region,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/sea-ice/{forecast_id}", response_model=ForecastResult)
async def get_sea_ice_forecast(
    forecast_id: uuid.UUID,
    db: AsyncSession = Depends(deps.get_db),
) -> Any:
    """Retrieve a persisted forecast by id."""
    obj = await forecast_repo.get(db, forecast_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Forecast not found")
    return ForecastResult(
        forecast_id=str(obj.id),
        grid_metadata={"resolution": "10km", "crs": "EPSG:4326"},
        timestamp=obj.created_at,
        horizon_days=obj.forecast_horizon_days,
        region=obj.region,
        predicted_concentration=obj.predicted_concentration,
        confidence=obj.confidence,
        model_metadata=obj.model_metadata,
        quality_flags=obj.quality_flags,
    )
