import json
import sys
sys.path.insert(0, "/Users/apple/Downloads/offshore")
from ml.inference.seaice_predict import predict_sea_ice_concentration

base_kwargs = {
    "latitude": -67.5,
    "longitude": -45.0,
    "sea_ice_concentration": 0.45,
    "air_temperature_c": -14.0,
    "sea_surface_temperature_c": -0.5,
    "sea_level_pressure_hpa": 1000.0,
    "wind_speed_m_s": 8.0,
    "wind_u_m_s": 4.0,
    "wind_v_m_s": -4.0,
    "current_speed_m_s": 0.1,
    "current_u_m_s": 0.08,
    "current_v_m_s": -0.03,
    "sea_surface_height_anomaly_cm": 0.0,
    "forecast_horizon_hours": 24,
    "timestamp": "2026-09-24T12:00:00Z"
}

res_a = predict_sea_ice_concentration(**base_kwargs)
pred_a = res_a['predicted_sea_ice_concentration']

b_kwargs = base_kwargs.copy()
b_kwargs["air_temperature_c"] = -30.0
res_b = predict_sea_ice_concentration(**b_kwargs)
pred_b = res_b['predicted_sea_ice_concentration']

print(f"Prediction A (Air Temp -14.0C): {pred_a}")
print(f"Prediction B (Air Temp -30.0C): {pred_b}")
print(f"Difference: {pred_b - pred_a}")
