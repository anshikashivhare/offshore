import os
import pandas as pd
import numpy as np
from pathlib import Path

# Paths
RAW_DIR = Path("/Users/apple/Downloads/data/raw")
PROCESSED_DIR = Path("/Users/apple/Downloads/ml/data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def haversine_distances(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dphi/2)**2 + np.cos(phi1)*np.cos(phi2)*np.sin(dlon/2)**2
    return 2 * R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

def assign_nearest_cell(df_target, df_grid, lat_col="latitude_t", lon_col="longitude_t"):
    print("Assigning nearest grid cells (this may take a moment)...")
    grid_lats = df_grid["latitude"].values
    grid_lons = df_grid["longitude"].values
    cell_ids = []
    
    # Simple loop for brevity and guaranteed correct haversine distance
    for _, row in df_target.iterrows():
        dists = haversine_distances(row[lat_col], row[lon_col], grid_lats, grid_lons)
        nearest_idx = np.argmin(dists)
        cell_ids.append(df_grid.iloc[nearest_idx]["cell_id"])
        
    df_target = df_target.copy()
    df_target["cell_id"] = np.array(cell_ids, dtype=np.int64)
    return df_target

def main():
    print("Loading datasets...")
    df_ib = pd.read_csv(RAW_DIR / "iceberg_trajectory_synthetic_2026.csv", parse_dates=["timestamp"])
    df_wx = pd.read_csv(RAW_DIR / "weather_synthetic_2026.csv", parse_dates=["timestamp"])
    df_oc = pd.read_csv(RAW_DIR / "ocean_currents_synthetic_2026.csv", parse_dates=["timestamp"])
    df_si = pd.read_csv(RAW_DIR / "sea_ice_synthetic_2026.csv", parse_dates=["timestamp"])
    df_grid = pd.read_csv(RAW_DIR / "grid_cells_2026.csv")
    
    print(f"Original iceberg rows: {len(df_ib)}")
    
    # 1. Drop old invalid environment columns from iceberg
    pure_ib_cols = [
        "sample_id", "iceberg_id", "timestamp", 
        "latitude_t_minus_2", "longitude_t_minus_2",
        "latitude_t_minus_1", "longitude_t_minus_1",
        "latitude_t", "longitude_t",
        "forecast_horizon_hours", "target_latitude", "target_longitude", 
        "data_status", "data_source_type"
    ]
    df_ib_pure = df_ib[pure_ib_cols].copy()
    
    # 2. Assign nearest cell
    df_ib_cells = assign_nearest_cell(df_ib_pure, df_grid)
    
    # 3. Prepare environmental data (rolling 24h averages as in sea ice)
    print("Preparing 24h rolling environmental features...")
    wx_features = ['air_temperature_c', 'sea_level_pressure_hpa', 'wind_speed_m_s', 'wind_u_m_s', 'wind_v_m_s']
    oc_features = ['current_u_m_s', 'current_v_m_s', 'current_speed_m_s', 'sea_surface_height_anomaly_cm']
    
    df_env = pd.merge(
        df_wx[['cell_id', 'timestamp'] + wx_features],
        df_oc[['cell_id', 'timestamp'] + oc_features],
        on=['cell_id', 'timestamp']
    )
    df_env = df_env.sort_values(['cell_id', 'timestamp'])
    
    env_features = wx_features + oc_features
    df_env_rolling = (
        df_env.groupby('cell_id')[env_features]
        .rolling(window=4, min_periods=1)
        .mean()
        .reset_index(level=0, drop=True)
    )
    df_env_agg = df_env[['cell_id', 'timestamp']].copy()
    df_env_agg[env_features] = df_env_rolling[env_features]
    
    # 4. As-of Join for Weather/Ocean (Tolerance 6 hours)
    print("Aligning weather & ocean data...")
    df_ib_cells = df_ib_cells.sort_values("timestamp")
    df_env_agg = df_env_agg.sort_values("timestamp")
    
    df_aligned = pd.merge_asof(
        df_ib_cells,
        df_env_agg,
        on="timestamp",
        by="cell_id",
        direction="backward",
        tolerance=pd.Timedelta(hours=6)
    )
    
    # 5. As-of Join for Sea Ice (Tolerance 24 hours because sea ice is daily)
    print("Aligning sea ice data...")
    df_si_sub = df_si[["cell_id", "timestamp", "sea_ice_concentration", "sea_surface_temperature_c"]].copy()
    df_si_sub = df_si_sub.sort_values("timestamp")
    
    df_aligned = pd.merge_asof(
        df_aligned,
        df_si_sub,
        on="timestamp",
        by="cell_id",
        direction="backward",
        tolerance=pd.Timedelta(hours=24)
    )
    
    # 6. Report and save
    missing = df_aligned.isnull().sum()
    print("\nMissing values after alignment:")
    print(missing[missing > 0])
    
    if missing.sum() > 0:
        print("Warning: some matches failed. Filling with median for training compatibility.")
        df_aligned = df_aligned.fillna(df_aligned.median(numeric_only=True))
        
    output_path = PROCESSED_DIR / "iceberg_aligned_2026.csv"
    df_aligned.to_csv(output_path, index=False)
    print(f"\nSaved aligned iceberg dataset to {output_path}")
    print(f"Final dataset shape: {df_aligned.shape}")
    print(f"Columns: {df_aligned.columns.tolist()}")

if __name__ == "__main__":
    main()
