"""
Iceberg Trajectory XGBoost Training Pipeline  ·  SIH 2026 PS-26059
===================================================================
Uses SYNTHETIC CSV data. Results are prototype-only and do NOT represent
real Antarctic iceberg tracking measurements.

Run:
    cd /Users/apple/Downloads/offshore
    source .venv/bin/activate
    python ml/training/iceberg_xgb_train.py
"""

import json
import math
import sys
import time
import uuid
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# 0. Paths
# ─────────────────────────────────────────────────────────────────────────────
RAW_CSV       = Path("/Users/apple/Downloads/ml/data/raw/iceberg_trajectory_synthetic.csv")
PROCESSED_DIR = Path("/Users/apple/Downloads/ml/data/processed")
MODEL_DIR     = Path("/Users/apple/Downloads/offshore/ml/models/weights")
REPORTS_DIR   = Path("/Users/apple/Downloads/ml/reports")

for d in [PROCESSED_DIR, MODEL_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

print("=" * 60)
print("  ICEBERG TRAJECTORY XGBOOST PIPELINE  [SYNTHETIC DATA]")
print("=" * 60)

t0 = time.time()

# ─────────────────────────────────────────────────────────────────────────────
# 1. Load & validate
# ─────────────────────────────────────────────────────────────────────────────
df = pd.read_csv(RAW_CSV)
df.columns = df.columns.str.strip()           # strip \r artefacts
print(f"\n[1] Loaded {len(df):,} rows from {RAW_CSV.name}")

REQUIRED_RAW = [
    "iceberg_id", "timestamp",
    "latitude_t_minus_2", "longitude_t_minus_2",
    "latitude_t_minus_1", "longitude_t_minus_1",
    "latitude_t",         "longitude_t",
    "wind_speed_m_s",     "wind_direction_deg",
    "ocean_current_u_m_s", "ocean_current_v_m_s",
    "sea_ice_concentration", "forecast_horizon_hours",
    "target_latitude",    "target_longitude",
    "data_source_type",
]
missing_raw = [c for c in REQUIRED_RAW if c not in df.columns]
if missing_raw:
    sys.exit(f"ERROR: Missing raw columns: {missing_raw}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Validation
# ─────────────────────────────────────────────────────────────────────────────
print("\n[2] Data Validation")

val_report = {
    "total_rows": int(len(df)),
    "total_cols": int(len(df.columns)),
    "icebergs":   int(df["iceberg_id"].nunique()),
    "missing":    int(df[REQUIRED_RAW].isnull().sum().sum()),
    "duplicates": int(df.duplicated().sum()),
    "data_source_type": df["data_source_type"].str.strip().unique().tolist(),
    "forecast_horizon_hours_values": df["forecast_horizon_hours"].unique().tolist(),
    "lat_range": [float(df["latitude_t"].min()), float(df["latitude_t"].max())],
    "lon_range": [float(df["longitude_t"].min()), float(df["longitude_t"].max())],
    "sic_range": [float(df["sea_ice_concentration"].min()),
                  float(df["sea_ice_concentration"].max())],
}

print(f"  Rows: {val_report['total_rows']:,}  |  Icebergs: {val_report['icebergs']}")
print(f"  Missing: {val_report['missing']}  |  Duplicates: {val_report['duplicates']}")
print(f"  Latitude range: {val_report['lat_range']}")
print(f"  data_source_type: {val_report['data_source_type']}")

if df["latitude_t"].max() > -50:
    print("  WARNING: Some latitudes are outside expected Antarctic range (<-50°)")
if not (0 <= df["sea_ice_concentration"].min() and df["sea_ice_concentration"].max() <= 1):
    print("  WARNING: sea_ice_concentration outside [0, 1]")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Preprocessing & feature engineering
# ─────────────────────────────────────────────────────────────────────────────
print("\n[3] Preprocessing")

df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values(["iceberg_id", "timestamp"]).reset_index(drop=True)

# Velocity history: displacement between lagged positions (degrees per step)
df["dlat_1"] = df["latitude_t"]       - df["latitude_t_minus_1"]
df["dlon_1"] = df["longitude_t"]       - df["longitude_t_minus_1"]
df["dlat_2"] = df["latitude_t_minus_1"] - df["latitude_t_minus_2"]
df["dlon_2"] = df["longitude_t_minus_1"] - df["longitude_t_minus_2"]

# Approximate speed (degrees/step as proxy — no real unit conversion needed for XGBoost)
df["speed_1"] = np.sqrt(df["dlat_1"] ** 2 + df["dlon_1"] ** 2)
df["speed_2"] = np.sqrt(df["dlat_2"] ** 2 + df["dlon_2"] ** 2)

# Wind decomposition (avoids direction circularity)
df["wind_u"] = df["wind_speed_m_s"] * np.cos(np.radians(df["wind_direction_deg"]))
df["wind_v"] = df["wind_speed_m_s"] * np.sin(np.radians(df["wind_direction_deg"]))

# Temporal
df["month"]   = df["timestamp"].dt.month
df["sin_doy"] = np.sin(2 * np.pi * df["timestamp"].dt.dayofyear / 365.25)
df["cos_doy"] = np.cos(2 * np.pi * df["timestamp"].dt.dayofyear / 365.25)

# Target: delta from current position (predicting movement, not absolute coords)
# This is more stable than predicting absolute lat/lon
df["target_dlat"] = df["target_latitude"]  - df["latitude_t"]
df["target_dlon"]  = df["target_longitude"] - df["longitude_t"]

FEATURE_COLS = [
    "latitude_t", "longitude_t",
    "dlat_1", "dlon_1",
    "dlat_2", "dlon_2",
    "speed_1", "speed_2",
    "wind_u", "wind_v",
    "ocean_current_u_m_s", "ocean_current_v_m_s",
    "sea_ice_concentration",
    "forecast_horizon_hours",
    "month", "sin_doy", "cos_doy",
]
TARGET_LAT = "target_dlat"
TARGET_LON  = "target_dlon"

# Sanity check
inf_count = np.isinf(df[FEATURE_COLS].values).sum()
nan_count = df[FEATURE_COLS + [TARGET_LAT, TARGET_LON]].isnull().sum().sum()
if inf_count > 0:
    print(f"  WARNING: {inf_count} infinite values — replacing")
    df[FEATURE_COLS] = df[FEATURE_COLS].replace([np.inf, -np.inf], np.nan)
if nan_count > 0:
    print(f"  WARNING: {nan_count} NaN values — filling with median")
    df[FEATURE_COLS] = df[FEATURE_COLS].fillna(df[FEATURE_COLS].median())

print(f"  Feature columns ({len(FEATURE_COLS)}): {FEATURE_COLS}")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Per-iceberg chronological split (70 / 15 / 15)
#    Split WITHIN each iceberg's track, so training always uses earlier
#    positions and test uses later positions. This prevents temporal leakage.
# ─────────────────────────────────────────────────────────────────────────────
print("\n[4] Per-Iceberg Chronological Split (70 / 15 / 15)")

train_frames, val_frames, test_frames = [], [], []

for iceberg_id, group in df.groupby("iceberg_id"):
    group = group.sort_values("timestamp")
    n = len(group)
    val_idx  = int(n * 0.70)
    test_idx = int(n * 0.85)
    train_frames.append(group.iloc[:val_idx])
    val_frames.append(group.iloc[val_idx:test_idx])
    test_frames.append(group.iloc[test_idx:])

train_df = pd.concat(train_frames).reset_index(drop=True)
val_df   = pd.concat(val_frames).reset_index(drop=True)
test_df  = pd.concat(test_frames).reset_index(drop=True)

print(f"  Train: {len(train_df):,} rows  |  Val: {len(val_df):,}  |  Test: {len(test_df):,}")

X_train  = train_df[FEATURE_COLS].values
ylat_train = train_df[TARGET_LAT].values
ylon_train  = train_df[TARGET_LON].values

X_val    = val_df[FEATURE_COLS].values
ylat_val   = val_df[TARGET_LAT].values
ylon_val    = val_df[TARGET_LON].values

X_test   = test_df[FEATURE_COLS].values
ylat_test  = test_df[TARGET_LAT].values
ylon_test   = test_df[TARGET_LON].values

# Save processed splits
train_df.to_csv(PROCESSED_DIR / "iceberg_train.csv", index=False)
val_df.to_csv(PROCESSED_DIR   / "iceberg_val.csv",   index=False)
test_df.to_csv(PROCESSED_DIR  / "iceberg_test.csv",  index=False)
print(f"  Splits saved to {PROCESSED_DIR}")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Persistence baseline (predict zero movement)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[5] Persistence Baseline (zero movement)")

rmse_lat_persist = math.sqrt(np.mean(ylat_test ** 2))
rmse_lon_persist = math.sqrt(np.mean(ylon_test ** 2))

# Haversine distance error for persistence
lat_t_test = test_df["latitude_t"].values
lon_t_test = test_df["longitude_t"].values
true_lat   = lat_t_test + ylat_test
true_lon   = lon_t_test + ylon_test
pred_lat_persist = lat_t_test        # zero movement
pred_lon_persist = lon_t_test

def haversine_km_array(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = phi2 - phi1
    dl   = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

dist_persist_km = haversine_km_array(true_lat, true_lon, pred_lat_persist, pred_lon_persist)
print(f"  Persistence RMSE lat: {rmse_lat_persist:.5f}°  lon: {rmse_lon_persist:.5f}°")
print(f"  Persistence mean position error: {dist_persist_km.mean():.3f} km")

# ─────────────────────────────────────────────────────────────────────────────
# 6. Train two XGBoost models (one per target dimension)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[6] Training XGBoost (lat + lon separately)")

try:
    import xgboost as xgb
    print(f"  xgboost version: {xgb.__version__}")
except ImportError:
    sys.exit("ERROR: xgboost not installed")

xgb_params = {
    "n_estimators":    300,
    "learning_rate":   0.05,
    "max_depth":       5,
    "subsample":       0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 3,
    "reg_alpha":       0.1,
    "reg_lambda":      1.0,
    "objective":       "reg:squarederror",
    "tree_method":     "hist",
    "random_state":    42,
    "n_jobs":          -1,
}

t_train = time.time()

model_lat = xgb.XGBRegressor(**xgb_params)
model_lat.fit(X_train, ylat_train,
              eval_set=[(X_val, ylat_val)], verbose=50)

model_lon = xgb.XGBRegressor(**xgb_params)
model_lon.fit(X_train, ylon_train,
              eval_set=[(X_val, ylon_val)], verbose=50)

train_time = time.time() - t_train
print(f"  Training time: {train_time:.1f}s")

# ─────────────────────────────────────────────────────────────────────────────
# 7. Evaluate on test set
# ─────────────────────────────────────────────────────────────────────────────
print("\n[7] Evaluation on Test Set")

t_inf = time.time()
pred_dlat = model_lat.predict(X_test)
pred_dlon  = model_lon.predict(X_test)
inf_time   = time.time() - t_inf

mae_lat  = float(np.mean(np.abs(ylat_test - pred_dlat)))
rmse_lat = math.sqrt(float(np.mean((ylat_test - pred_dlat) ** 2)))
mae_lon  = float(np.mean(np.abs(ylon_test - pred_dlon)))
rmse_lon  = math.sqrt(float(np.mean((ylon_test - pred_dlon) ** 2)))

ss_res_lat = np.sum((ylat_test - pred_dlat) ** 2)
ss_tot_lat = np.sum((ylat_test - ylat_test.mean()) ** 2)
r2_lat = float(1 - ss_res_lat / ss_tot_lat) if ss_tot_lat > 0 else float("nan")

ss_res_lon = np.sum((ylon_test - pred_dlon) ** 2)
ss_tot_lon = np.sum((ylon_test - ylon_test.mean()) ** 2)
r2_lon = float(1 - ss_res_lon / ss_tot_lon) if ss_tot_lon > 0 else float("nan")

# Haversine position error
pred_abs_lat = lat_t_test + pred_dlat
pred_abs_lon = lon_t_test + pred_dlon
dist_xgb_km  = haversine_km_array(true_lat, true_lon, pred_abs_lat, pred_abs_lon)

print(f"  Δlat — MAE: {mae_lat:.5f}°  RMSE: {rmse_lat:.5f}°  R²: {r2_lat:.4f}")
print(f"  Δlon — MAE: {mae_lon:.5f}°  RMSE: {rmse_lon:.5f}°  R²: {r2_lon:.4f}")
print(f"  Mean position error: {dist_xgb_km.mean():.3f} km")
print(f"  Median position error: {np.median(dist_xgb_km):.3f} km")
print(f"  P95 position error: {np.percentile(dist_xgb_km, 95):.3f} km")
print(f"  Inference time for {len(X_test)} samples: {inf_time*1000:.1f} ms")
print()
print(f"  --- Comparison vs baseline ---")
print(f"  Persistence mean pos error: {dist_persist_km.mean():.3f} km")
print(f"  XGBoost   mean pos error:   {dist_xgb_km.mean():.3f} km")
improvement = (dist_persist_km.mean() - dist_xgb_km.mean()) / dist_persist_km.mean() * 100
print(f"  Improvement: {improvement:.1f}%")

# ─────────────────────────────────────────────────────────────────────────────
# 8. Save artifacts
# ─────────────────────────────────────────────────────────────────────────────
print("\n[8] Saving Artifacts")

run_id = str(uuid.uuid4())[:8]
lat_model_path    = MODEL_DIR / f"iceberg_xgb_lat_{run_id}.json"
lon_model_path    = MODEL_DIR / f"iceberg_xgb_lon_{run_id}.json"
lat_latest_path   = MODEL_DIR / "iceberg_xgb_lat_latest.json"
lon_latest_path   = MODEL_DIR / "iceberg_xgb_lon_latest.json"
schema_path       = MODEL_DIR / "iceberg_feature_schema.json"
report_path       = REPORTS_DIR / f"iceberg_eval_report_{run_id}.json"

model_lat.save_model(str(lat_model_path))
model_lat.save_model(str(lat_latest_path))
model_lon.save_model(str(lon_model_path))
model_lon.save_model(str(lon_latest_path))
print(f"  lat model: {lat_latest_path}")
print(f"  lon model: {lon_latest_path}")

schema = {
    "run_id":         run_id,
    "feature_cols":   FEATURE_COLS,
    "target_lat_col": TARGET_LAT,
    "target_lon_col": TARGET_LON,
    "xgb_params":     xgb_params,
    "data_source":    "SYNTHETIC_PROTOTYPE",
    "dataset_path":   str(RAW_CSV),
    "n_train": int(len(X_train)),
    "n_val":   int(len(X_val)),
    "n_test":  int(len(X_test)),
    "preprocessing": {
        "wind_decomposed": True,
        "velocity_lag_features": True,
        "targets": "delta from current position (degrees)",
        "split_method": "per_iceberg_chronological_70_15_15",
    },
}
with open(schema_path, "w") as f:
    json.dump(schema, f, indent=2)

eval_report = {
    "run_id":          run_id,
    "data_source":     "SYNTHETIC_PROTOTYPE",
    "warning":         "Results on synthetic data do NOT establish real-world accuracy.",
    "n_train": int(len(X_train)),
    "n_val":   int(len(X_val)),
    "n_test":  int(len(X_test)),
    "training_time_s":   round(train_time, 2),
    "inference_time_ms": round(inf_time * 1000, 2),
    "persistence_baseline": {
        "rmse_lat_deg":      round(rmse_lat_persist, 5),
        "rmse_lon_deg":      round(rmse_lon_persist, 5),
        "mean_pos_error_km": round(float(dist_persist_km.mean()), 3),
    },
    "xgboost": {
        "mae_lat":           round(mae_lat, 5),
        "rmse_lat":          round(rmse_lat, 5),
        "r2_lat":            round(r2_lat, 4),
        "mae_lon":           round(mae_lon, 5),
        "rmse_lon":          round(rmse_lon, 5),
        "r2_lon":            round(r2_lon, 4),
        "mean_pos_error_km": round(float(dist_xgb_km.mean()), 3),
        "median_pos_error_km": round(float(np.median(dist_xgb_km)), 3),
        "p95_pos_error_km":  round(float(np.percentile(dist_xgb_km, 95)), 3),
    },
    "improvement_over_baseline_pct": round(improvement, 1),
    "lat_model_path": str(lat_latest_path),
    "lon_model_path": str(lon_latest_path),
    "schema_path":    str(schema_path),
}
with open(report_path, "w") as f:
    json.dump(eval_report, f, indent=2)

print(f"  Schema: {schema_path}")
print(f"  Report: {report_path}")

total_time = time.time() - t0
print(f"\n{'='*60}")
print(f"  TRAINING COMPLETE  [{total_time:.1f}s total]  Run ID: {run_id}")
print(f"{'='*60}")
