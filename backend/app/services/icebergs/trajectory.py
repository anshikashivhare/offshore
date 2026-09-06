from __future__ import annotations

import logging
import math
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.iceberg import IcebergDetection, IcebergTrajectoryPrediction
from app.models.observation import OceanObservation, WeatherObservation
from app.repositories.iceberg import iceberg_prediction as prediction_repo
from app.schemas.common import GeoJSONFeature
from app.schemas.iceberg import IcebergTrajectoryPredictionProperties
from app.utils.geometry_decode import geometry_centroid_lonlat

logger = logging.getLogger(__name__)


EARTH_RADIUS_KM = 6371.0088


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2.0) ** 2
    )
    return 2.0 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def _km_per_deg_lat() -> float:
    return math.pi * EARTH_RADIUS_KM / 180.0


def _km_per_deg_lon(lat: float) -> float:
    return math.pi * EARTH_RADIUS_KM * math.cos(math.radians(lat)) / 180.0


class IcebergTrajectoryPredictor(ABC):
    """Abstract base class for predicting iceberg trajectories."""

    @abstractmethod
    async def predict_trajectory(
        self,
        iceberg_id: uuid.UUID,
        historical_track: List[GeoJSONFeature],
        environmental_conditions: Dict[str, Any],
        horizon_hours: int,
        start_time: datetime,
    ) -> List[GeoJSONFeature[IcebergTrajectoryPredictionProperties]]: ...


class PhysicsBasedTrajectoryPredictor(IcebergTrajectoryPredictor):
    """Drift the iceberg along the latest ocean-current and wind vectors.

    For each hourly step the iceberg is advected using:

        v_lat_km_per_h = ocean_current_speed * cos(theta_ocean) * windage
        v_lon_km_per_h = ocean_current_speed * sin(theta_ocean) * windage

    where ``windage`` is a small fraction of wind influence (default 0.02, i.e.
    2% of wind). The drift is converted to degrees using a local lat/lon
    scaling factor. Uncertainty grows as ``radius_km = base + growth_per_hour * h``
    and is rendered as a square bounding box around the predicted point.
    """

    def __init__(
        self,
        db: AsyncSession,
        *,
        windage: float = 0.02,
        uncertainty_base_km: float = 1.0,
        uncertainty_growth_km_per_h: float = 0.5,
        model_version: str = "physics_v1.0",
    ):
        self.db = db
        self.windage = windage
        self.uncertainty_base_km = uncertainty_base_km
        self.uncertainty_growth_km_per_h = uncertainty_growth_km_per_h
        self.model_version = model_version

    async def _latest_environment(
        self, lat: float, lon: float, ref_time: datetime
    ) -> Dict[str, float]:
        envelope = func.ST_MakeEnvelope(
            lon - 5.0, lat - 5.0, lon + 5.0, lat + 5.0, 4326
        )
        oc = None
        wx = None
        oc_geom = getattr(OceanObservation, "geometry", None)
        if oc_geom is not None and getattr(oc_geom, "ST_Intersects", None) is not None:
            oc = (
                await self.db.execute(
                    select(OceanObservation)
                    .where(OceanObservation.geometry.ST_Intersects(envelope))
                    .where(OceanObservation.timestamp <= ref_time)
                    .order_by(OceanObservation.timestamp.desc())
                    .limit(1)
                )
            ).scalars().first()
        else:
            oc = (
                await self.db.execute(
                    select(OceanObservation)
                    .where(OceanObservation.timestamp <= ref_time)
                    .order_by(OceanObservation.timestamp.desc())
                    .limit(1)
                )
            ).scalars().first()
        wx_geom = getattr(WeatherObservation, "geometry", None)
        if wx_geom is not None and getattr(wx_geom, "ST_Intersects", None) is not None:
            wx = (
                await self.db.execute(
                    select(WeatherObservation)
                    .where(WeatherObservation.geometry.ST_Intersects(envelope))
                    .where(WeatherObservation.timestamp <= ref_time)
                    .order_by(WeatherObservation.timestamp.desc())
                    .limit(1)
                )
            ).scalars().first()
        else:
            wx = (
                await self.db.execute(
                    select(WeatherObservation)
                    .where(WeatherObservation.timestamp <= ref_time)
                    .order_by(WeatherObservation.timestamp.desc())
                    .limit(1)
                )
            ).scalars().first()
        env: Dict[str, float] = {
            "current_speed_mps": 0.0,
            "current_direction_deg": 0.0,
            "wind_speed_mps": 0.0,
            "wind_direction_deg": 0.0,
        }
        if oc is not None:
            env["current_speed_mps"] = float(oc.current_speed or 0.0)
            env["current_direction_deg"] = float(oc.current_direction or 0.0)
        if wx is not None:
            env["wind_speed_mps"] = float(wx.wind_speed or 0.0)
            env["wind_direction_deg"] = float(wx.wind_direction or 0.0)
        return env

    async def predict_trajectory(
        self,
        iceberg_id: uuid.UUID,
        historical_track: List[GeoJSONFeature],
        environmental_conditions: Dict[str, Any],
        horizon_hours: int,
        start_time: datetime,
    ) -> List[GeoJSONFeature[IcebergTrajectoryPredictionProperties]]:
        if horizon_hours <= 0:
            return []

        if historical_track:
            last = historical_track[-1]
            cur_lon, cur_lat = last.geometry["coordinates"][:2]
        else:
            cur_lon, cur_lat = 0.0, 0.0

        env = environmental_conditions or await self._latest_environment(
            cur_lat, cur_lon, start_time
        )
        current_speed_mps = float(env.get("current_speed_mps", 0.0))
        current_dir = math.radians(float(env.get("current_direction_deg", 0.0)))
        wind_speed_mps = float(env.get("wind_speed_mps", 0.0))
        wind_dir = math.radians(float(env.get("wind_direction_deg", 0.0)))

        v_north_mps = current_speed_mps * math.cos(current_dir) + (
            self.windage * wind_speed_mps * math.cos(wind_dir)
        )
        v_east_mps = current_speed_mps * math.sin(current_dir) + (
            self.windage * wind_speed_mps * math.sin(wind_dir)
        )

        lat, lon = cur_lat, cur_lon
        path: List[List[float]] = [[lon, lat]]
        for h in range(1, horizon_hours + 1):
            km_per_deg_lat = _km_per_deg_lat()
            km_per_deg_lon = max(1e-6, _km_per_deg_lon(lat))
            dlat = (v_north_mps * 3600.0) / 1000.0 / km_per_deg_lat
            dlon = (v_east_mps * 3600.0) / 1000.0 / km_per_deg_lon
            lat += dlat
            lon += dlon
            path.append([lon, lat])

        predictions: List[GeoJSONFeature[IcebergTrajectoryPredictionProperties]] = []
        last_pred = prediction_repo is None  # type: ignore[comparison-overlap]
        for hour, (lon_h, lat_h) in enumerate(path[1:], start=1):
            radius_km = self.uncertainty_base_km + self.uncertainty_growth_km_per_h * hour
            dlat_deg = radius_km / _km_per_deg_lat()
            dlon_deg = radius_km / max(1e-6, _km_per_deg_lon(lat_h))
            poly_coords = [
                [lon_h - dlon_deg, lat_h - dlat_deg],
                [lon_h + dlon_deg, lat_h - dlat_deg],
                [lon_h + dlon_deg, lat_h + dlat_deg],
                [lon_h - dlon_deg, lat_h + dlat_deg],
                [lon_h - dlon_deg, lat_h - dlat_deg],
            ]
            confidence = max(0.1, 1.0 - 0.01 * hour)
            ts = start_time + timedelta(hours=hour)
            prediction_id = uuid.uuid4()

            props = IcebergTrajectoryPredictionProperties(
                id=prediction_id,
                iceberg_id=iceberg_id,
                prediction_timestamp=ts,
                forecast_horizon=hour,
                uncertainty_representation=(
                    f"POLYGON(({poly_coords[0][0]} {poly_coords[0][1]},"
                    f" {poly_coords[1][0]} {poly_coords[1][1]},"
                    f" {poly_coords[2][0]} {poly_coords[2][1]},"
                    f" {poly_coords[3][0]} {poly_coords[3][1]},"
                    f" {poly_coords[0][0]} {poly_coords[0][1]}))"
                ),
                model_confidence=confidence,
                model_version=self.model_version,
            )
            feature = GeoJSONFeature[IcebergTrajectoryPredictionProperties](
                type="Feature",
                geometry={
                    "type": "Polygon",
                    "coordinates": [poly_coords],
                },
                properties=props,
            )
            predictions.append(feature)

            try:
                await prediction_repo.create(
                    self.db,
                    obj_in={
                        "id": prediction_id,
                        "iceberg_id": iceberg_id,
                        "prediction_timestamp": ts,
                        "forecast_horizon": hour,
                        "forecast_horizon_unit": "hours",
                        "predicted_geometry": f"POINT({lon_h} {lat_h})",
                        "predicted_path": path[: hour + 1],
                        "uncertainty_representation": (
                            f"POLYGON(({poly_coords[0][0]} {poly_coords[0][1]},"
                            f" {poly_coords[1][0]} {poly_coords[1][1]},"
                            f" {poly_coords[2][0]} {poly_coords[2][1]},"
                            f" {poly_coords[3][0]} {poly_coords[3][1]},"
                            f" {poly_coords[0][0]} {poly_coords[0][1]}))"
                        ),
                        "model_confidence": confidence,
                        "model_version": self.model_version,
                    },
                )
            except Exception as exc:
                logger.warning("Failed to persist prediction %s: %s", prediction_id, exc)

        await self.db.commit()
        return predictions


# Backwards compatibility alias used by tests / earlier code.
BaselineTrajectoryPredictor = PhysicsBasedTrajectoryPredictor


def calculate_ade(y_true_coords: np.ndarray, y_pred_coords: np.ndarray) -> float:
    """Average Displacement Error (ADE). Mean Euclidean distance over all predicted points."""
    if len(y_true_coords) == 0 or len(y_true_coords) != len(y_pred_coords):
        raise ValueError("Arrays must be of equal, non-zero length.")
    distances = np.linalg.norm(y_true_coords - y_pred_coords, axis=1)
    return float(np.mean(distances))


def calculate_fde(y_true_coords: np.ndarray, y_pred_coords: np.ndarray) -> float:
    """Final Displacement Error (FDE). Euclidean distance between final points."""
    if len(y_true_coords) == 0 or len(y_true_coords) != len(y_pred_coords):
        raise ValueError("Arrays must be of equal, non-zero length.")
    final_true = y_true_coords[-1]
    final_pred = y_pred_coords[-1]
    return float(np.linalg.norm(final_true - final_pred))