import os
import pandas as pd
import numpy as np
import torch
import json

print("--- PHASE 1: DATASET INVENTORY & AUDIT ---")
csv_path = "ml/data/raw/iceberg_trajectory_synthetic_2026.csv"
if not os.path.exists(csv_path):
    print("Dataset not found!")
    exit(1)

df = pd.read_csv(csv_path)
print(f"Total rows: {len(df)}")
print(f"Columns: {list(df.columns)}")
print(f"Unique iceberg_ids: {df['iceberg_id'].nunique()}")

# Phase 2: Trajectory Integrity
icebergs = df.groupby('iceberg_id')
traj_lengths = icebergs.size()
print(f"\n--- PHASE 2: TRAJECTORY INTEGRITY ---")
print(f"Observations per iceberg (Mean): {traj_lengths.mean():.2f}")
print(f"Median length: {traj_lengths.median()}")
print(f"Min length: {traj_lengths.min()}")
print(f"Max length: {traj_lengths.max()}")

# Sort and check timestamps
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values(by=['iceberg_id', 'timestamp'])

# Time deltas
def get_time_deltas(group):
    return group['timestamp'].diff().dt.total_seconds() / 3600.0

time_deltas = df.groupby('iceberg_id').apply(get_time_deltas, include_groups=False).dropna()
print(f"\nTime intervals between observations (hours):")
print(f"Mean: {time_deltas.mean():.2f}h, Min: {time_deltas.min()}h, Max: {time_deltas.max()}h")

print("\n--- PHASE 3: SPATIAL INTEGRITY ---")
print(f"Latitude range: {df['latitude_t'].min():.4f} to {df['latitude_t'].max():.4f}")
print(f"Longitude range: {df['longitude_t'].min():.4f} to {df['longitude_t'].max():.4f}")

# Phase 5: Target Definition Check
print("\n--- PHASE 5: TARGET DEFINITION ---")
print("We want to predict trajectory displacement or future positions.")
print("Existing variables suggest predicting target_latitude and target_longitude or displacement.")

print("\n--- PHASE 14: EXISTING ARTIFACT AUDIT ---")
artifact_path = "ml/models/weights/iceberg_lstm_v001.pt"
if os.path.exists(artifact_path):
    print("Artifact found. Attempting to load state_dict...")
    try:
        sd = torch.load(artifact_path, map_location="cpu", weights_only=False)
        print(f"Loaded successfully. Type: {type(sd)}")
        if isinstance(sd, dict):
            print(f"Keys: {list(sd.keys())}")
    except Exception as e:
        print(f"Failed to load: {e}")
else:
    print("Artifact not found.")
