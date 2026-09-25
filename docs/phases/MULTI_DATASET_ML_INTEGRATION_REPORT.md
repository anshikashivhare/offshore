# MULTI-DATASET ML INTEGRATION REPORT
**Project:** SIH 26059 - Antarctic Navigation
**Phase:** 0 - Freeze Existing Working Pipeline

## 1. Dataset Inventory
*Pending new dataset intakes.*

## 2. Dataset Provenance
*Pending new dataset intakes.*

## 3. Schema Comparison
**Baseline (Current Working Prototype)**
- **Model:** `seaice_xgb_latest.json`
- **Hash:** `0074c7f040ba860effcf25ddfecf05d1c9ea0d67d5dc6e6c629f6cdb28266ca1`
- **Features Used:** `latitude`, `longitude`, `sea_ice_concentration`, `air_temperature_c`, `sea_surface_temperature_c`, `sea_level_pressure_hpa`, `wind_speed_m_s`, `wind_u_m_s`, `wind_v_m_s`, `current_speed_m_s`, `current_u_m_s`, `current_v_m_s`, `sea_surface_height_anomaly_cm`, `forecast_horizon_hours`, `month`, `sin_doy`, `cos_doy`
- **Target:** `target_sea_ice_concentration`

## 4. Spatial Alignment
*Pending new dataset intakes.*

## 5. Temporal Alignment
*Pending new dataset intakes.*

## 6. Units
*Pending new dataset intakes.*

## 7. Quality Control
**Baseline Parameters:**
- Infinite values replaced with NaN.
- NaN values filled with column median.
- Missing required inference features (from live environment) fall back to sensible defaults.

## 8. Leakage Audit
**Baseline Status:**
- Temporal: `day_of_year`, `month`, `sin_doy`, `cos_doy` derived purely from observation timestamp.
- No future observations used in historical features.
- Train/Val/Test Split: Chronological (70% / 15% / 15%).

## 9. Synthetic vs Real Data
**Baseline:**
- Current model (`seaice_xgb_latest.json`) is trained on **SYNTHETIC_PROTOTYPE** data.
- Inference is verified against **REAL_LIVE** environment data.
- Status flag (`data_source_type: SYNTHETIC_PROTOTYPE`) is passed through to predictions.

## 10. Feature Engineering
**Baseline:**
- `sin_doy`, `cos_doy` for cyclical seasonality.
- `timestamp` removed to prevent explicit memorization.

## 11. Training Strategy
**Baseline:**
- XGBoost Regressor.
- Separate prototype train scripts for Sea Ice and Iceberg Trajectory.

## 12. Model Comparison
*Pending new model training.*

## 13. Validation Results
*Pending new model validation.*

## 14. Artifact Versions
- Baseline: `seaice_xgb_latest.json` (SHA256: `0074c7f040ba860effcf25ddfecf05d1c9ea0d67d5dc6e6c629f6cdb28266ca1`)

## 15. Inference Compatibility
**Baseline:**
- Evaluated via `ml/evaluation/baseline_test_suite.py`
- Test suite successfully loads the artifact and verifies exact schema matching the live inference endpoint.

## 16. Backend Integration
**Baseline:**
- `app.services.forecasting.ml_forecaster.MLForecaster` successfully calls `predict_sea_ice_concentration`.

## 17. Route Integration
**Baseline:**
- A* planner retrieves risk.
- Risk scales with `predicted_sea_ice_concentration_clipped`.

## 18. Known Limitations
- Current model is synthetic.
- Does not contain real satellite observation targets.

## 19. Recommended Dataset Gaps
- Needs real observational sea ice coverage (e.g., NSIDC).
- Needs real iceberg trajectory history (e.g., Brigham Young University dataset).
- Needs real historic weather/wave/current data corresponding to the observations.

## 20. Exact Commands Executed
- `shasum -a 256 ml/models/weights/seaice_xgb_latest.json`
- `mkdir -p ml/evaluation`
- Created `ml/evaluation/baseline_test_suite.py`
- `.venv/bin/python ml/evaluation/baseline_test_suite.py`
