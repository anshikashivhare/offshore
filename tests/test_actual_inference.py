import sys
from pathlib import Path

# Setup path for backend
_root = str(Path(__file__).resolve().parents[0])
if _root not in sys.path:
    sys.path.insert(0, _root)

from ml.inference import seaice_predict
seaice_predict._MODEL_PATH = Path(_root) / "ml" / "models" / "weights" / "seaice_xgb_v002.json"

try:
    res = seaice_predict.predict_sea_ice_concentration(
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
        timestamp="2026-10-01T12:00:00Z"
        # model_version parameter might not exist.
    )
    print("Inference completed with Old baseline. Output:", res)
    
except Exception as e:
    print(f"Error testing inference: {e}")
