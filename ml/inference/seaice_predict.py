"""
Sea-Ice Concentration Inference Module
SIH 2026 PS-26059  ·  SYNTHETIC_PROTOTYPE

Provides a reusable prediction function that accepts validated input features
and returns predicted future sea-ice concentration with metadata.

The output can be consumed by the risk engine and route engine.
Do NOT claim this model determines whether a vessel route is safe independently.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Any, Optional

# Default model paths
_MODEL_DIR   = Path(__file__).parent.parent / "models" / "weights"
_MODEL_PATH  = _MODEL_DIR / "seaice_xgb_latest.json"
_SCHEMA_PATH = _MODEL_DIR / "seaice_feature_schema.json"

_model  = None
_schema = None


def _load_model():
    """Lazy-load the XGBoost model (singleton)."""
    global _model, _schema
    if _model is None:
        try:
            import xgboost as xgb
        except ImportError:
            raise ImportError("xgboost is required. Install with: pip install xgboost")
        _model = xgb.XGBRegressor()
        _model.load_model(str(_MODEL_PATH))
        with open(_SCHEMA_PATH, "r") as f:
            _schema = json.load(f)
    return _model, _schema


def predict_sea_ice_concentration(
    latitude: float,
    longitude: float,
    sea_ice_concentration: float,
    air_temperature_c: float,
    sea_surface_temperature_c: float,
    ocean_current_u_m_s: float,
    ocean_current_v_m_s: float,
    wind_speed_m_s: float,
    wind_direction_deg: float,
    forecast_horizon_hours: int = 24,
    timestamp: Optional[str] = None,
) -> dict[str, Any]:
    """
    Predict future sea-ice concentration using the trained XGBoost model.

    Returns dict with:
        - predicted_sea_ice_concentration         : float, raw model output
        - predicted_sea_ice_concentration_clipped : float, clipped to [0, 1]
        - forecast_horizon_hours                  : int
        - data_source_type                        : "SYNTHETIC_PROTOTYPE"
        - model_run_id                            : str
        - features_used                           : dict
        - warning                                 : str
    """
    model, schema = _load_model()

    # Temporal features
    ts      = pd.Timestamp(timestamp) if timestamp else pd.Timestamp.utcnow()
    month   = ts.month
    doy     = ts.day_of_year
    sin_doy = float(np.sin(2 * np.pi * doy / 365.25))
    cos_doy = float(np.cos(2 * np.pi * doy / 365.25))

    # Wind decomposition
    wind_u = wind_speed_m_s * np.cos(np.radians(wind_direction_deg))
    wind_v = wind_speed_m_s * np.sin(np.radians(wind_direction_deg))

    feature_vals = {
        "latitude":                  latitude,
        "longitude":                 longitude,
        "sea_ice_concentration":     sea_ice_concentration,
        "air_temperature_c":         air_temperature_c,
        "sea_surface_temperature_c": sea_surface_temperature_c,
        "ocean_current_u_m_s":       ocean_current_u_m_s,
        "ocean_current_v_m_s":       ocean_current_v_m_s,
        "forecast_horizon_hours":    forecast_horizon_hours,
        "month":                     month,
        "sin_doy":                   sin_doy,
        "cos_doy":                   cos_doy,
        "wind_u":                    wind_u,
        "wind_v":                    wind_v,
    }

    if not (-90 <= latitude <= -50):
        raise ValueError(f"latitude {latitude} outside expected Antarctic range [-90, -50]")
    if not (0.0 <= sea_ice_concentration <= 1.0):
        raise ValueError(f"sea_ice_concentration {sea_ice_concentration} must be in [0, 1]")

    expected_cols = schema["feature_cols"]
    X = pd.DataFrame([{c: feature_vals[c] for c in expected_cols}])

    raw_pred     = float(model.predict(X.values)[0])
    clipped_pred = float(np.clip(raw_pred, 0.0, 1.0))

    return {
        "predicted_sea_ice_concentration":         raw_pred,
        "predicted_sea_ice_concentration_clipped": clipped_pred,
        "forecast_horizon_hours":                  forecast_horizon_hours,
        "data_source_type":                        "SYNTHETIC_PROTOTYPE",
        "model_run_id":                            schema.get("run_id", "unknown"),
        "features_used":                           feature_vals,
        "warning": (
            "This model was trained on SYNTHETIC data. "
            "It does NOT represent validated real-world Antarctic sea-ice forecasting. "
            "Do not use standalone for vessel safety decisions."
        ),
    }


# ─── Legacy interface (backwards-compat with existing seaice_train.py) ───────

import joblib as _joblib

try:
    from ml.path_utils import get_model_path as _get_model_path
except ImportError:
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from ml.path_utils import get_model_path as _get_model_path

_legacy_model = None
_LEGACY_PATH  = _get_model_path("seaice_xgb.joblib")
FEATURE_COLS  = ["lag_1", "lag_2", "lag_3", "day_of_year", "lat", "lon"]


def load_model(path=_LEGACY_PATH):
    global _legacy_model
    if _legacy_model is None and Path(path).exists():
        _legacy_model = _joblib.load(path)
    return _legacy_model


def predict_concentration(lag_1, lag_2, lag_3, day_of_year, lat, lon):
    """Single-cell forecast using legacy RandomForest model (if available)."""
    model = load_model()
    if model is None:
        raise FileNotFoundError(
            f"Legacy model not found at {_LEGACY_PATH}. "
            "Use predict_sea_ice_concentration() instead."
        )
    X = pd.DataFrame([{"lag_1": lag_1, "lag_2": lag_2, "lag_3": lag_3,
                        "day_of_year": day_of_year, "lat": lat, "lon": lon}])[FEATURE_COLS]
    return float(model.predict(X)[0])


if __name__ == "__main__":
    result = predict_sea_ice_concentration(
        latitude=-67.5,
        longitude=-45.0,
        sea_ice_concentration=0.45,
        air_temperature_c=-14.0,
        sea_surface_temperature_c=-0.5,
        ocean_current_u_m_s=0.08,
        ocean_current_v_m_s=-0.03,
        wind_speed_m_s=8.0,
        wind_direction_deg=270.0,
        forecast_horizon_hours=24,
    )
    print(json.dumps(
        {k: v for k, v in result.items() if k != "features_used"}, indent=2
    ))
