import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

print("--- PHASE 1: TRACE SPARSITY ORIGIN ---")

# Paths
raw_sea_ice = "ml/data/raw/sea_ice_synthetic_2026.csv"
raw_weather = "ml/data/raw/weather_synthetic_2026.csv"
raw_currents = "ml/data/raw/ocean_currents_synthetic_2026.csv"
processed_aligned = "ml/data/processed/aligned_environment_v2.csv"

def get_stats(path):
    if not os.path.exists(path):
        return {"exists": False}
    # Load first 500k rows if big, or just full if small enough.
    # The synthetic files are 6MB, 65MB, 43MB. We can load them entirely into pandas.
    df = pd.read_csv(path)
    timestamps = df['timestamp'].unique()
    cells = df.groupby('timestamp')['cell_id'].nunique()
    total_unique_cells = df['cell_id'].nunique()
    return {
        "exists": True,
        "rows": len(df),
        "unique_timestamps": len(timestamps),
        "total_unique_cells": total_unique_cells,
        "avg_cells_per_timestamp": cells.mean(),
        "min_cells_per_timestamp": cells.min(),
        "max_cells_per_timestamp": cells.max()
    }

print("Analyzing raw sea_ice...")
stats_si = get_stats(raw_sea_ice)
print(stats_si)

print("Analyzing raw weather...")
stats_we = get_stats(raw_weather)
print(stats_we)

print("Analyzing raw ocean currents...")
stats_oc = get_stats(raw_currents)
print(stats_oc)

print("Analyzing processed aligned...")
stats_proc = get_stats(processed_aligned)
print(stats_proc)


print("\n--- PHASE 2 & 3: SPATIAL DISTRIBUTION & TEMPORAL STABILITY ---")
df_proc = pd.read_csv(processed_aligned)
lats = np.sort(df_proc['latitude'].unique())
lons = np.sort(df_proc['longitude'].unique())

H, W = len(lats), len(lons)
print(f"Global Extent: H={H} (lats), W={W} (lons)")

t_groups = df_proc.groupby('timestamp')
first_timestamp = list(t_groups.groups.keys())[0]
df_t0 = t_groups.get_group(first_timestamp)

plt.figure(figsize=(10, 8))
plt.scatter(df_t0['longitude'], df_t0['latitude'], c='blue', s=20, label='Valid Cells at T0')
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.title(f"Spatial Distribution of Valid Cells (T0 = {first_timestamp})")
plt.grid(True)
plt.legend()
plt.savefig("ml/evaluation/sparsity_spatial_dist.png")
print("Saved spatial scatter plot to ml/evaluation/sparsity_spatial_dist.png")

# Check temporal stability
cells_per_t = df_proc.groupby('timestamp')['cell_id'].apply(set)
first_set = cells_per_t.iloc[0]
intersection_all = set(first_set)
for s in cells_per_t:
    intersection_all = intersection_all.intersection(s)

print(f"Cells present at T0: {len(first_set)}")
print(f"Cells present across ALL timestamps: {len(intersection_all)}")

# Let's see if it's a corridor
lat_range = df_t0['latitude'].max() - df_t0['latitude'].min()
lon_range = df_t0['longitude'].max() - df_t0['longitude'].min()
print(f"Spatial spread of the 50 valid cells: lat_range={lat_range:.2f} deg, lon_range={lon_range:.2f} deg")

print("\n--- PHASE 4: JOIN DIAGNOSIS ---")
# Let's see if raw sea ice had only 50 cells too
if stats_si['exists']:
    print(f"Raw sea ice avg cells per timestamp: {stats_si['avg_cells_per_timestamp']}")
    if stats_si['avg_cells_per_timestamp'] == 50.0:
        print("ROOT CAUSE FOUND: The raw sea_ice dataset itself only contains 50 spatial cells per timestamp!")
        print("The sparsity is INTRINSIC to the source data (likely sampled along a specific ship corridor or 50 observation stations), not caused by preprocessing joins.")
    else:
        print("ROOT CAUSE LIKELY IN JOIN: The raw data had more cells, but joining reduced it to 50.")
