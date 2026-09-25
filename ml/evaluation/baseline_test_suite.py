import json
import pytest
from pathlib import Path
import sys
import datetime

# Fix path to load inference
_root = str(Path(__file__).resolve().parents[2])
if _root not in sys.path:
    sys.path.insert(0, _root)

from ml.inference.seaice_predict import predict_sea_ice_concentration

def test_model_artifact_exists():
    """Phase 0: Ensure the frozen model artifact remains available."""
    model_path = Path(_root) / "ml" / "models" / "weights" / "seaice_xgb_latest.json"
    assert model_path.exists(), "The currently verified model artifact is missing!"

def test_inference_schema_compatibility():
    """Phase 0: Ensure the API contract and inference schema do not break."""
    res = predict_sea_ice_concentration(
        latitude=-65.0,
        longitude=-60.0,
        sea_ice_concentration=0.5,
        air_temperature_c=-10.0,
        sea_surface_temperature_c=-1.0,
        sea_level_pressure_hpa=1000.0,
        wind_speed_m_s=5.0,
        wind_u_m_s=0.0,
        wind_v_m_s=0.0,
        current_speed_m_s=0.1,
        current_u_m_s=0.0,
        current_v_m_s=0.0,
        sea_surface_height_anomaly_cm=0.0,
        forecast_horizon_hours=24,
        timestamp=datetime.datetime.utcnow().isoformat()
    )
    
    assert "predicted_sea_ice_concentration_clipped" in res
    assert 0.0 <= res["predicted_sea_ice_concentration_clipped"] <= 1.0
    
    # Metadata should remain consistent
    assert "features_used" in res
    features = res["features_used"]
    assert "sin_doy" in features
    assert "cos_doy" in features
    assert "month" in features

if __name__ == "__main__":
    pytest.main(["-v", __file__])
