"""
Iceberg Trajectory Inference Module
SIH 2026 PS-26059  ·  SYNTHETIC_PROTOTYPE

Provides predict_iceberg_trajectory() for use by the risk engine and
route engine. Predicts delta-lat / delta-lon from the current position.

Do NOT claim this model independently determines vessel safety.
"""

import json
import math
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Optional

_MODEL_DIR       = Path(__file__).parent.parent / "models" / "weights"
_LAT_MODEL_PATH  = _MODEL_DIR / "iceberg_xgb_lat_latest.json"
_LON_MODEL_PATH  = _MODEL_DIR / "iceberg_xgb_lon_latest.json"
_SCHEMA_PATH     = _MODEL_DIR / "iceberg_feature_schema.json"

_model_lat = None
_model_lon = None
_schema    = None


def _load_models():
    global _model_lat, _model_lon, _schema
    if _model_lat is None:
        try:
            import xgboost as xgb
        except ImportError:
            raise ImportError("xgboost required: pip install xgboost")
        _model_lat = xgb.XGBRegressor()
        _model_lat.load_model(str(_LAT_MODEL_PATH))
        _model_lon = xgb.XGBRegressor()
        _model_lon.load_model(str(_LON_MODEL_PATH))
        with open(_SCHEMA_PATH) as f:
            _schema = json.load(f)
    return _model_lat, _model_lon, _schema


def predict_iceberg_trajectory(
    latitude_t: float,
    longitude_t: float,
    latitude_t_minus_1: float,
    longitude_t_minus_1: float,
    latitude_t_minus_2: float,
    longitude_t_minus_2: float,
    wind_speed_m_s: float,
    wind_direction_deg: float,
    ocean_current_u_m_s: float,
    ocean_current_v_m_s: float,
    sea_ice_concentration: float,
    forecast_horizon_hours: int = 6,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Predict next iceberg position given current + lag positions + environment.

    Returns:
        predicted_delta_lat  : float, degrees
        predicted_delta_lon  : float, degrees
        predicted_latitude   : float, degrees (absolute)
        predicted_longitude  : float, degrees (absolute)
        forecast_horizon_hours : int
        data_source_type     : "SYNTHETIC_PROTOTYPE"
        model_run_id         : str
        warning              : str
    """
    model_lat, model_lon, schema = _load_models()

    if not (-90 <= latitude_t <= -50):
        raise ValueError(f"latitude_t {latitude_t} outside Antarctic range [-90, -50]")
    if not (0.0 <= sea_ice_concentration <= 1.0):
        raise ValueError(f"sea_ice_concentration {sea_ice_concentration} must be in [0, 1]")

    ts = pd.Timestamp(timestamp) if timestamp else pd.Timestamp.utcnow()

    dlat_1 = latitude_t       - latitude_t_minus_1
    dlon_1 = longitude_t      - longitude_t_minus_1
    dlat_2 = latitude_t_minus_1 - latitude_t_minus_2
    dlon_2 = longitude_t_minus_1 - longitude_t_minus_2
    speed_1 = math.sqrt(dlat_1 ** 2 + dlon_1 ** 2)
    speed_2 = math.sqrt(dlat_2 ** 2 + dlon_2 ** 2)

    wind_u = wind_speed_m_s * np.cos(np.radians(wind_direction_deg))
    wind_v = wind_speed_m_s * np.sin(np.radians(wind_direction_deg))

    feature_vals = {
        "latitude_t":            latitude_t,
        "longitude_t":           longitude_t,
        "dlat_1":                dlat_1,
        "dlon_1":                dlon_1,
        "dlat_2":                dlat_2,
        "dlon_2":                dlon_2,
        "speed_1":               speed_1,
        "speed_2":               speed_2,
        "wind_u":                float(wind_u),
        "wind_v":                float(wind_v),
        "ocean_current_u_m_s":   ocean_current_u_m_s,
        "ocean_current_v_m_s":   ocean_current_v_m_s,
        "sea_ice_concentration":  sea_ice_concentration,
        "forecast_horizon_hours": forecast_horizon_hours,
        "month":                 ts.month,
        "sin_doy":               float(np.sin(2 * np.pi * ts.day_of_year / 365.25)),
        "cos_doy":               float(np.cos(2 * np.pi * ts.day_of_year / 365.25)),
    }

    expected_cols = schema["feature_cols"]
    X = np.array([[feature_vals[c] for c in expected_cols]])

    pred_dlat = float(model_lat.predict(X)[0])
    pred_dlon  = float(model_lon.predict(X)[0])

    return {
        "predicted_delta_lat":    pred_dlat,
        "predicted_delta_lon":    pred_dlon,
        "predicted_latitude":     latitude_t + pred_dlat,
        "predicted_longitude":    longitude_t + pred_dlon,
        "forecast_horizon_hours": forecast_horizon_hours,
        "data_source_type":       "SYNTHETIC_PROTOTYPE",
        "model_run_id":           schema.get("run_id", "unknown"),
        "warning": (
            "Trained on SYNTHETIC data only. "
            "Does NOT represent validated real-world iceberg trajectory forecasting. "
            "Do not use standalone for vessel safety decisions."
        ),
    }


# ─── Legacy interface compat (used by backend/app/main.py eager load) ─────────

import joblib as _joblib

try:
    from ml.path_utils import get_model_path as _get_model_path
except ImportError:
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from ml.path_utils import get_model_path as _get_model_path

FEATURE_COLS  = ["lat", "lon", "current_u", "current_v", "wind_u", "wind_v"]
_legacy_model = None
_LEGACY_PATH  = _get_model_path("trajectory_model.joblib")


def load_model(path: str = _LEGACY_PATH):
    """Legacy load — used by backend app startup for eager pre-load."""
    global _legacy_model
    if _legacy_model is None and Path(path).exists():
        _legacy_model = _joblib.load(path)
    return _legacy_model


def predict_next_step(lat, lon, current_u, current_v, wind_u, wind_v):
    """Legacy single-step prediction (RandomForest model if available)."""
    model = load_model()
    if model is None:
        raise FileNotFoundError(
            f"Legacy model not found at {_LEGACY_PATH}. "
            "Use predict_iceberg_trajectory() instead."
        )
    X = pd.DataFrame([{"lat": lat, "lon": lon,
                        "current_u": current_u, "current_v": current_v,
                        "wind_u": wind_u, "wind_v": wind_v}])[FEATURE_COLS]
    delta_lat, delta_lon = model.predict(X)[0]
    return float(delta_lat), float(delta_lon)


def project_trajectory(lat, lon, current_u, current_v, wind_u, wind_v, num_steps=5):
    path = [{"lat": lat, "lon": lon}]
    for _ in range(num_steps):
        delta_lat, delta_lon = predict_next_step(lat, lon, current_u, current_v, wind_u, wind_v)
        lat += delta_lat
        lon += delta_lon
        path.append({"lat": round(lat, 5), "lon": round(lon, 5)})
    return path


if __name__ == "__main__":
    result = predict_iceberg_trajectory(
        latitude_t=-65.5,     longitude_t=61.7,
        latitude_t_minus_1=-65.54, longitude_t_minus_1=61.65,
        latitude_t_minus_2=-65.58, longitude_t_minus_2=61.61,
        wind_speed_m_s=2.0,   wind_direction_deg=315.0,
        ocean_current_u_m_s=0.18, ocean_current_v_m_s=0.09,
        sea_ice_concentration=0.35, forecast_horizon_hours=6,
    )
    print(json.dumps({k: v for k, v in result.items()}, indent=2))
