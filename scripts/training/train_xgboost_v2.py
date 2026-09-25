import os
import json
import hashlib
import datetime
from pathlib import Path

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Paths
processed_data = Path("ml/data/processed/aligned_environment_v2.csv")
baseline_model = Path("ml/models/weights/seaice_xgb_latest.json")
new_model_path = Path("ml/models/weights/seaice_xgb_v002.json")
new_metadata_path = Path("ml/models/metadata/seaice_xgb_v002.json")
metrics_path = Path("ml/evaluation/seaice_xgb_v002_metrics.json")
error_analysis_path = Path("ml/evaluation/seaice_xgb_v002_error_analysis.json")
manifest_path = Path("ml/experiments/training_manifest_v2.json")

for p in [new_metadata_path.parent, metrics_path.parent, manifest_path.parent]:
    p.mkdir(parents=True, exist_ok=True)

# 1. Load Data
df = pd.read_csv(processed_data)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values('timestamp').reset_index(drop=True)

# 2. Freeze Splits (70/15/15)
n = len(df)
train_end = int(n * 0.70)
val_end = int(n * 0.85)

train_df = df.iloc[:train_end].copy()
val_df = df.iloc[train_end:val_end].copy()
test_df = df.iloc[val_end:].copy()

target = 'target_sea_ice_concentration'
features = [
    'latitude', 'longitude', 'sea_ice_concentration', 'air_temperature_c',
    'sea_surface_temperature_c', 'sea_level_pressure_hpa', 'wind_speed_m_s',
    'wind_u_m_s', 'wind_v_m_s', 'current_speed_m_s', 'current_u_m_s', 'current_v_m_s',
    'sea_surface_height_anomaly_cm', 'forecast_horizon_hours'
]

# Extract time-based features
for split_df in [train_df, val_df, test_df]:
    split_df['month'] = split_df['timestamp'].dt.month
    doy = split_df['timestamp'].dt.dayofyear
    split_df['sin_doy'] = np.sin(2 * np.pi * doy / 365.25)
    split_df['cos_doy'] = np.cos(2 * np.pi * doy / 365.25)

features += ['month', 'sin_doy', 'cos_doy']

X_train, y_train = train_df[features], train_df[target]
X_val, y_val = val_df[features], val_df[target]
X_test, y_test = test_df[features], test_df[target]

# 3. Persistence Baseline
persistence_preds = test_df['sea_ice_concentration'].values
persistence_rmse = np.sqrt(mean_squared_error(y_test, persistence_preds))
persistence_mae = mean_absolute_error(y_test, persistence_preds)

# 4. Old Baseline Evaluation
old_model = xgb.XGBRegressor()
old_model.load_model(baseline_model)

# The old model doesn't have current_direction_deg, etc. We must match exactly its schema
old_features = [
    'latitude', 'longitude', 'sea_ice_concentration', 'air_temperature_c',
    'sea_surface_temperature_c', 'sea_level_pressure_hpa', 'wind_speed_m_s',
    'wind_u_m_s', 'wind_v_m_s', 'current_speed_m_s', 'current_u_m_s', 'current_v_m_s',
    'sea_surface_height_anomaly_cm', 'forecast_horizon_hours', 'month', 'sin_doy', 'cos_doy'
]
X_test_old = test_df[old_features]
old_preds = old_model.predict(X_test_old)
old_rmse = np.sqrt(mean_squared_error(y_test, old_preds))
old_mae = mean_absolute_error(y_test, old_preds)

# 5. Train New Candidate (XGBoost v2)
# Bounded grid search (simple loop for minimal search)
best_rmse = float('inf')
best_model = None
best_params = {}

for max_depth in [4, 6]:
    for lr in [0.05, 0.1]:
        model = xgb.XGBRegressor(
            n_estimators=300,
            max_depth=max_depth,
            learning_rate=lr,
            random_state=42,
            n_jobs=8,
            early_stopping_rounds=20
        )
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        preds = model.predict(X_val)
        rmse = np.sqrt(mean_squared_error(y_val, preds))
        if rmse < best_rmse:
            best_rmse = rmse
            best_model = model
            best_params = {'max_depth': max_depth, 'learning_rate': lr, 'n_estimators': 300}

# 6. Evaluate New Candidate
new_preds = best_model.predict(X_test)
# Clip to physical bounds
new_preds_clipped = np.clip(new_preds, 0.0, 1.0)
new_rmse = np.sqrt(mean_squared_error(y_test, new_preds_clipped))
new_mae = mean_absolute_error(y_test, new_preds_clipped)

# 7. Metrics & Artifact Registration
best_model.save_model(new_model_path)
with open(new_model_path, 'rb') as f:
    artifact_hash = hashlib.sha256(f.read()).hexdigest()

metrics = {
    'persistence': {'RMSE': float(persistence_rmse), 'MAE': float(persistence_mae)},
    'old_baseline': {'RMSE': float(old_rmse), 'MAE': float(old_mae)},
    'new_candidate': {'RMSE': float(new_rmse), 'MAE': float(new_mae)}
}
with open(metrics_path, 'w') as f:
    json.dump(metrics, f, indent=2)

manifest = {
    "experiment_id": "exp_v002",
    "timestamp": datetime.datetime.utcnow().isoformat(),
    "processed_dataset": str(processed_data),
    "target": target,
    "features": features,
    "train_period": [str(train_df['timestamp'].min()), str(train_df['timestamp'].max())],
    "test_period": [str(test_df['timestamp'].min()), str(test_df['timestamp'].max())],
    "hyperparameters": best_params,
    "artifact_hash": artifact_hash
}
with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2)

print("Training execution complete. Metrics:", json.dumps(metrics, indent=2))
