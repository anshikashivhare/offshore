import os
import pandas as pd
import numpy as np
from pathlib import Path

# Paths
RAW_DIR = Path("/Users/apple/Downloads/data/raw")
PROCESSED_DIR = Path("/Users/apple/Downloads/ml/data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

print("Loading raw 2026 datasets...")
df_si = pd.read_csv(RAW_DIR / "sea_ice_synthetic_2026.csv", parse_dates=["timestamp"])
df_wx = pd.read_csv(RAW_DIR / "weather_synthetic_2026.csv", parse_dates=["timestamp"])
df_oc = pd.read_csv(RAW_DIR / "ocean_currents_synthetic_2026.csv", parse_dates=["timestamp"])

print(f"Original sea ice rows: {len(df_si)}")

# 1. Strip bad pre-merged weather/ocean columns from sea ice data
pure_si_cols = [
    "sample_id", "cell_id", "timestamp", "latitude", "longitude", 
    "sea_ice_concentration", "forecast_horizon_hours", 
    "target_sea_ice_concentration", "data_status", "data_source_type"
]
# Retain sea_surface_temperature_c as it comes natively with the sea ice observation dataset
df_si_pure = df_si[pure_si_cols + ['sea_surface_temperature_c']].copy()

# 2. Prepare environmental data
print("Merging weather and ocean currents...")
wx_features = ['air_temperature_c', 'sea_level_pressure_hpa', 'wind_speed_m_s', 'wind_u_m_s', 'wind_v_m_s']
oc_features = ['current_u_m_s', 'current_v_m_s', 'current_speed_m_s', 'sea_surface_height_anomaly_cm']

df_env = pd.merge(
    df_wx[['cell_id', 'timestamp'] + wx_features],
    df_oc[['cell_id', 'timestamp'] + oc_features],
    on=['cell_id', 'timestamp']
)

# 3. Compute 24-hour backward rolling average
print("Computing 24-hour rolling averages for environmental features...")
df_env = df_env.sort_values(['cell_id', 'timestamp'])
env_features = wx_features + oc_features

# Using rolling window of 4 steps (since data is 6h intervals, 4 steps = 24 hours including the current step)
df_env_rolling = (
    df_env.groupby('cell_id')[env_features]
    .rolling(window=4, min_periods=1)
    .mean()
    .reset_index(level=0, drop=True)
)

# Re-attach keys
df_env_agg = df_env[['cell_id', 'timestamp']].copy()
df_env_agg[env_features] = df_env_rolling[env_features]

# 4. Merge aggregated features onto sea ice timestamps
print("Aligning aggregated features with sea ice observation times...")
df_aligned = pd.merge(df_si_pure, df_env_agg, on=['cell_id', 'timestamp'], how='left')

missing = df_aligned.isnull().sum().sum()
if missing > 0:
    print(f"Warning: {missing} missing values after merge. Filling with median.")
    df_aligned = df_aligned.fillna(df_aligned.median(numeric_only=True))

output_path = PROCESSED_DIR / "sea_ice_aligned_2026.csv"
df_aligned.to_csv(output_path, index=False)
print(f"\nSaved aligned dataset to {output_path}")
print(f"Final dataset shape: {df_aligned.shape}")
print(f"Columns: {df_aligned.columns.tolist()}")
