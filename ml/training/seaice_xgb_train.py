"""
Sea-Ice XGBoost Training Pipeline  ·  SIH 2026 PS-26059
========================================================
Uses SYNTHETIC CSV data. Results are prototype-only and do NOT represent
real Antarctic satellite measurements.

Run:
    python -m ml.training.seaice_xgb_train
or:
    python /Users/apple/Downloads/offshore/ml/training/seaice_xgb_train.py
"""

import json
import os
import sys
import time
import uuid
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
# 0. Paths
# ─────────────────────────────────────────────────────────────
RAW_CSV       = Path("/Users/apple/Downloads/ml/data/raw/sea_ice_synthetic.csv")
PROCESSED_DIR = Path("/Users/apple/Downloads/ml/data/processed")
MODEL_DIR     = Path("/Users/apple/Downloads/offshore/ml/models/weights")
REPORTS_DIR   = Path("/Users/apple/Downloads/ml/reports")

for d in [PROCESSED_DIR, MODEL_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# 1. Load & validate
# ─────────────────────────────────────────────────────────────
print("=" * 60)
print("  SEA-ICE XGBOOST TRAINING PIPELINE  [SYNTHETIC DATA]")
print("=" * 60)

t0 = time.time()
df = pd.read_csv(RAW_CSV)
print(f"\n[1] Loaded {len(df):,} rows from {RAW_CSV.name}")

REQUIRED_FEATURES = [
    "latitude", "longitude",
    "sea_ice_concentration",
    "air_temperature_c",
    "sea_surface_temperature_c",
    "wind_speed_m_s",
    "wind_direction_deg",
    "ocean_current_u_m_s",
    "ocean_current_v_m_s",
    "forecast_horizon_hours",
]
TARGET_COL = "target_sea_ice_concentration"

missing_cols = [c for c in REQUIRED_FEATURES + [TARGET_COL] if c not in df.columns]
if missing_cols:
    sys.exit(f"ERROR: Missing columns: {missing_cols}")

# ─────────────────────────────────────────────────────────────
# 2. Data validation report
# ─────────────────────────────────────────────────────────────
print("\n[2] Data Validation")

val_report = {}
val_report["total_rows"]     = int(len(df))
val_report["total_cols"]     = int(len(df.columns))
val_report["missing_values"] = df[REQUIRED_FEATURES + [TARGET_COL]].isnull().sum().to_dict()
val_report["duplicates"]     = int(df.duplicated().sum())
val_report["data_source_type_values"] = df["data_source_type"].unique().tolist()

# bounds
sic_min, sic_max = float(df["sea_ice_concentration"].min()), float(df["sea_ice_concentration"].max())
tgt_min, tgt_max = float(df[TARGET_COL].min()), float(df[TARGET_COL].max())
lat_min, lat_max = float(df["latitude"].min()),  float(df["latitude"].max())
val_report["sea_ice_concentration_range"] = [sic_min, sic_max]
val_report["target_range"] = [tgt_min, tgt_max]
val_report["latitude_range"] = [lat_min, lat_max]
val_report["longitude_range"] = [float(df["longitude"].min()), float(df["longitude"].max())]

if tgt_min < 0 or tgt_max > 1:
    print(f"  WARNING: target out of [0,1]: [{tgt_min:.4f}, {tgt_max:.4f}]")
else:
    print(f"  Target bounds OK: [{tgt_min:.4f}, {tgt_max:.4f}]")

if lat_min < -90 or lat_max > -50:
    print(f"  WARNING: latitude may be out of expected Antarctic range")
else:
    print(f"  Latitude range (Antarctic): [{lat_min:.2f}, {lat_max:.2f}]")

print(f"  Missing values: {sum(val_report['missing_values'].values())}")
print(f"  Duplicates: {val_report['duplicates']}")
print(f"  data_source_type: {val_report['data_source_type_values']}")

# ─────────────────────────────────────────────────────────────
# 3. Preprocessing
# ─────────────────────────────────────────────────────────────
print("\n[3] Preprocessing")

df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.sort_values("timestamp").reset_index(drop=True)

# Temporal features (no leakage — only derived from the observation timestamp)
df["day_of_year"] = df["timestamp"].dt.dayofyear
df["month"]       = df["timestamp"].dt.month
df["year"]        = df["timestamp"].dt.year
df["sin_doy"]     = np.sin(2 * np.pi * df["day_of_year"] / 365.25)
df["cos_doy"]     = np.cos(2 * np.pi * df["day_of_year"] / 365.25)

# Wind components from speed + direction (avoids circular discontinuity)
df["wind_u"] = df["wind_speed_m_s"] * np.cos(np.radians(df["wind_direction_deg"]))
df["wind_v"] = df["wind_speed_m_s"] * np.sin(np.radians(df["wind_direction_deg"]))

# Drop non-predictive cols
DROP_COLS = ["sample_id", "data_source_type", "timestamp",
             "wind_speed_m_s", "wind_direction_deg",
             "day_of_year", "year"]  # year removed to avoid spurious memorisation
df_model = df.drop(columns=DROP_COLS)

# Infinite / NaN check after feature engineering
inf_count  = np.isinf(df_model.select_dtypes("number")).sum().sum()
null_count = df_model.isnull().sum().sum()
if inf_count > 0:
    print(f"  WARNING: {inf_count} infinite values — replacing with NaN")
    df_model.replace([np.inf, -np.inf], np.nan, inplace=True)
if null_count > 0:
    print(f"  WARNING: {null_count} NaN values — filling with column median")
    df_model.fillna(df_model.median(numeric_only=True), inplace=True)

FEATURE_COLS = [c for c in df_model.columns if c != TARGET_COL]
print(f"  Feature columns ({len(FEATURE_COLS)}): {FEATURE_COLS}")

# ─────────────────────────────────────────────────────────────
# 4. Chronological train / val / test split  (70 / 15 / 15)
# ─────────────────────────────────────────────────────────────
print("\n[4] Chronological Split (70 / 15 / 15)")

n = len(df_model)
val_start  = int(n * 0.70)
test_start = int(n * 0.85)

train_df = df_model.iloc[:val_start].copy()
val_df   = df_model.iloc[val_start:test_start].copy()
test_df  = df_model.iloc[test_start:].copy()

print(f"  Train: {len(train_df):,} rows")
print(f"  Val:   {len(val_df):,} rows")
print(f"  Test:  {len(test_df):,} rows")

X_train = train_df[FEATURE_COLS].values
y_train = train_df[TARGET_COL].values
X_val   = val_df[FEATURE_COLS].values
y_val   = val_df[TARGET_COL].values
X_test  = test_df[FEATURE_COLS].values
y_test  = test_df[TARGET_COL].values

# Save processed splits for reference
train_df.to_csv(PROCESSED_DIR / "sea_ice_train.csv", index=False)
val_df.to_csv(PROCESSED_DIR   / "sea_ice_val.csv",   index=False)
test_df.to_csv(PROCESSED_DIR  / "sea_ice_test.csv",  index=False)
print("  Processed splits saved to:", PROCESSED_DIR)

# ─────────────────────────────────────────────────────────────
# 5. Persistence baseline (predict current SIC as forecast)
# ─────────────────────────────────────────────────────────────
print("\n[5] Persistence Baseline")

sic_col_idx     = FEATURE_COLS.index("sea_ice_concentration")
y_persist_test  = X_test[:, sic_col_idx]
mae_persist     = float(np.mean(np.abs(y_test - y_persist_test)))
rmse_persist    = float(np.sqrt(np.mean((y_test - y_persist_test) ** 2)))
ss_res = np.sum((y_test - y_persist_test) ** 2)
ss_tot = np.sum((y_test - y_test.mean()) ** 2)
r2_persist = float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")

print(f"  Persistence MAE:  {mae_persist:.4f}")
print(f"  Persistence RMSE: {rmse_persist:.4f}")
print(f"  Persistence R²:   {r2_persist:.4f}")

# ─────────────────────────────────────────────────────────────
# 6. Train XGBoost
# ─────────────────────────────────────────────────────────────
print("\n[6] Training XGBoost")

try:
    import xgboost as xgb
    print(f"  xgboost version: {xgb.__version__}")
except ImportError:
    sys.exit("ERROR: xgboost not installed. Run: pip install xgboost")

# Lean config for Colab Free / local CPU
xgb_params = {
    "n_estimators":          300,
    "learning_rate":         0.05,
    "max_depth":             5,
    "subsample":             0.8,
    "colsample_bytree":      0.8,
    "min_child_weight":      3,
    "reg_alpha":             0.1,
    "reg_lambda":            1.0,
    "objective":             "reg:squarederror",
    "tree_method":           "hist",   # histogram-based (fast, low-memory)
    "random_state":          42,
    "n_jobs":                -1,
}

model = xgb.XGBRegressor(**xgb_params)

t_train = time.time()
model.fit(
    X_train, y_train,
    eval_set=[(X_val, y_val)],
    verbose=50,
)
train_time = time.time() - t_train
print(f"  Training time: {train_time:.1f}s")

# ─────────────────────────────────────────────────────────────
# 7. Evaluate on test set
# ─────────────────────────────────────────────────────────────
print("\n[7] Evaluating on Test Set")

t_inf = time.time()
y_pred = model.predict(X_test)
inf_time = time.time() - t_inf

# Raw metrics (no clipping)
mae_xgb  = float(np.mean(np.abs(y_test - y_pred)))
rmse_xgb = float(np.sqrt(np.mean((y_test - y_pred) ** 2)))
ss_res   = np.sum((y_test - y_pred) ** 2)
r2_xgb   = float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")

# Clipped metrics (application output only)
y_pred_clipped = np.clip(y_pred, 0.0, 1.0)
mae_xgb_clip   = float(np.mean(np.abs(y_test - y_pred_clipped)))
rmse_xgb_clip  = float(np.sqrt(np.mean((y_test - y_pred_clipped) ** 2)))

out_of_bounds = int(np.sum((y_pred < 0) | (y_pred > 1)))

print(f"  XGBoost MAE  (raw):     {mae_xgb:.4f}")
print(f"  XGBoost RMSE (raw):     {rmse_xgb:.4f}")
print(f"  XGBoost R²   (raw):     {r2_xgb:.4f}")
print(f"  XGBoost MAE  (clipped): {mae_xgb_clip:.4f}")
print(f"  XGBoost RMSE (clipped): {rmse_xgb_clip:.4f}")
print(f"  Predictions out of [0,1]: {out_of_bounds}")
print(f"  Inference time for {len(X_test)} samples: {inf_time*1000:.1f} ms")
print()
print(f"  --- Comparison ---")
print(f"  Persistence RMSE: {rmse_persist:.4f}  |  XGBoost RMSE: {rmse_xgb:.4f}")
print(f"  Improvement over baseline: {(rmse_persist - rmse_xgb)/rmse_persist*100:.1f}%")

# ─────────────────────────────────────────────────────────────
# 8. Save model & artifacts
# ─────────────────────────────────────────────────────────────
print("\n[8] Saving Artifacts")

run_id = str(uuid.uuid4())[:8]
model_path   = MODEL_DIR / f"seaice_xgb_{run_id}.json"
default_path = MODEL_DIR / "seaice_xgb_latest.json"
schema_path  = MODEL_DIR / "seaice_feature_schema.json"
report_path  = REPORTS_DIR / f"eval_report_{run_id}.json"

# XGBoost model (portable JSON)
model.save_model(str(model_path))
model.save_model(str(default_path))
print(f"  Model saved: {model_path}")
print(f"  Latest symlink: {default_path}")

# Feature schema
schema = {
    "run_id":           run_id,
    "feature_cols":     FEATURE_COLS,
    "target_col":       TARGET_COL,
    "xgb_params":       xgb_params,
    "data_source":      "SYNTHETIC_PROTOTYPE",
    "dataset_path":     str(RAW_CSV),
    "n_train":          int(len(X_train)),
    "n_val":            int(len(X_val)),
    "n_test":           int(len(X_test)),
    "preprocessing": {
        "temporal_features": ["month", "sin_doy", "cos_doy"],
        "wind_decomposed":   True,
        "sort_by":           "timestamp",
        "split_method":      "chronological_70_15_15",
    },
}
with open(schema_path, "w") as f:
    json.dump(schema, f, indent=2)
print(f"  Feature schema: {schema_path}")

# Evaluation report
eval_report = {
    "run_id":             run_id,
    "data_source":        "SYNTHETIC_PROTOTYPE",
    "warning":            "Performance on synthetic data does NOT establish real-world Antarctic forecasting accuracy.",
    "n_train":            int(len(X_train)),
    "n_val":              int(len(X_val)),
    "n_test":             int(len(X_test)),
    "feature_cols":       FEATURE_COLS,
    "target_col":         TARGET_COL,
    "training_time_s":    round(train_time, 2),
    "inference_time_ms":  round(inf_time * 1000, 2),
    "persistence_baseline": {
        "mae":  round(mae_persist, 4),
        "rmse": round(rmse_persist, 4),
        "r2":   round(r2_persist, 4),
    },
    "xgboost": {
        "mae_raw":    round(mae_xgb, 4),
        "rmse_raw":   round(rmse_xgb, 4),
        "r2_raw":     round(r2_xgb, 4),
        "mae_clipped":  round(mae_xgb_clip, 4),
        "rmse_clipped": round(rmse_xgb_clip, 4),
        "predictions_out_of_bounds": out_of_bounds,
    },
    "improvement_over_baseline_pct": round((rmse_persist - rmse_xgb) / rmse_persist * 100, 1),
    "xgb_params": xgb_params,
    "model_path": str(default_path),
    "schema_path": str(schema_path),
    "validation_report": val_report,
}
with open(report_path, "w") as f:
    json.dump(eval_report, f, indent=2)

# Append to experiment log CSV
log_row = {
    "run_id":           run_id,
    "rmse_test":        round(rmse_xgb, 4),
    "mae_test":         round(mae_xgb, 4),
    "r2_test":          round(r2_xgb, 4),
    "rmse_baseline":    round(rmse_persist, 4),
    "improvement_pct":  round((rmse_persist - rmse_xgb) / rmse_persist * 100, 1),
    "n_train":          len(X_train),
    "n_val":            len(X_val),
    "n_test":           len(X_test),
    "model_path":       str(default_path),
}
log_path = REPORTS_DIR / "experiment_log.csv"
log_df   = pd.DataFrame([log_row])
if log_path.exists():
    log_df.to_csv(log_path, mode="a", header=False, index=False)
else:
    log_df.to_csv(log_path, index=False)

print(f"  Evaluation report: {report_path}")
print(f"  Experiment log:    {log_path}")

total_time = time.time() - t0
print(f"\n{'='*60}")
print(f"  TRAINING COMPLETE  [{total_time:.1f}s total]")
print(f"  Run ID: {run_id}")
print(f"{'='*60}")
