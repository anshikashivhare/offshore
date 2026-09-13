from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.models.forecast import Forecast
from app.models.observation import SeaIceObservation
from app.services.forecasting.base import SeaIceForecaster
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class BaselinePersistenceForecaster(SeaIceForecaster):
    """A baseline model that persists the most recent sea-ice concentration.

    Reads the latest ``SeaIceObservation`` rows inside the requested bbox and
    returns the average concentration as the persisted prediction. Confidence
    decays linearly with horizon. Replace with a real statistical or ML model
    by subclassing ``SeaIceForecaster``; no other code touches this class.
    """

    def __init__(self, db: Optional[AsyncSession] = None, model_version: str = "1.0"):
        self.db = db
        self.model_version = model_version

    async def predict(
        self, inputs: Any, horizon: int, region: Dict[str, float]
    ) -> Dict[str, Any]:
        if not isinstance(region, dict):
            raise ValueError(
                "region must be a dict with min_lon/min_lat/max_lon/max_lat."
            )

        concentrations: list[float] = []
        if self.db is not None:
            geom = getattr(SeaIceObservation, "geometry", None)
            stmt = select(SeaIceObservation)
            if geom is not None and getattr(geom, "ST_Intersects", None) is not None:
                envelope = func.ST_MakeEnvelope(
                    float(region.get("min_lon", -180)),
                    float(region.get("min_lat", -90)),
                    float(region.get("max_lon", 180)),
                    float(region.get("max_lat", 90)),
                    4326,
                )
                stmt = stmt.where(SeaIceObservation.geometry.ST_Intersects(envelope))
            stmt = stmt.order_by(SeaIceObservation.timestamp.desc()).limit(50)
            rows = (await self.db.execute(stmt)).scalars().all()
            concentrations = [float(r.concentration) for r in rows]

        if concentrations:
            avg_conc = sum(concentrations) / len(concentrations)
            data_quality = 0.85 if len(concentrations) >= 5 else 0.5
        else:
            avg_conc = 0.5
            data_quality = 0.2
            logger.warning(
                "Persistence forecaster found no SeaIceObservation rows in bbox; using fallback 0.5"
            )

        confidence = max(0.05, data_quality - 0.05 * max(0, horizon - 1))
        prediction_id = uuid.uuid4()

        result = {
            "forecast_id": str(prediction_id),
            "grid_metadata": {"resolution": "10km", "crs": "EPSG:4326"},
            "timestamp": datetime.now(timezone.utc),
            "horizon_days": horizon,
            "region": region,
            "predicted_concentration": avg_conc,
            "confidence": confidence,
            "model_metadata": self.get_metadata(),
            "quality_flags": ["baseline_persistence"]
            + ([] if concentrations else ["no_observations_in_bbox"]),
        }

        if self.db is not None:
            try:
                obj = Forecast(
                    id=prediction_id,
                    forecast_horizon_days=horizon,
                    initialization_time=result["timestamp"],
                    region=region,
                    predicted_concentration={
                        "mean": avg_conc,
                        "n_observations": len(concentrations),
                    },
                    confidence=confidence,
                    model_version=self.model_version,
                    model_metadata=self.get_metadata(),
                    quality_flags=result["quality_flags"],
                )
                self.db.add(obj)
                await self.db.commit()
            except Exception as exc:
                logger.warning("Failed to persist forecast %s: %s", prediction_id, exc)
                try:
                    await self.db.rollback()
                except Exception:
                    pass

        return result

    def validate_input(self, inputs: Any) -> bool:
        if not inputs:
            raise ValueError("Inputs cannot be empty for persistence forecasting.")
        return True

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": "Baseline Persistence",
            "version": self.model_version,
            "type": "statistical",
            "description": "Predicts future states as identical to the most recent observation.",
        }
