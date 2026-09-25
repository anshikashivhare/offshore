import os
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
import psutil

print("--- CONVLSTM PREFLIGHT SCRIPT ---")

# 1. Source Audit
csv_path = "ml/data/processed/aligned_environment_v2.csv"
if not os.path.exists(csv_path):
    print(f"Error: {csv_path} not found.")
    exit(1)

print(f"Loading {csv_path}...")
df = pd.read_csv(csv_path, nrows=500000) # load a chunk if too large, but 100k rows is usually small enough for memory
print(f"Loaded {len(df)} rows.")

# 2. Grid Reconstruction
lats = np.sort(df['latitude'].unique())
lons = np.sort(df['longitude'].unique())
lat_spacing = np.diff(lats) if len(lats) > 1 else [0]
lon_spacing = np.diff(lons) if len(lons) > 1 else [0]

H = len(lats)
W = len(lons)
print(f"Grid: H={H} (lats), W={W} (lons)")
print(f"Lat spacing: {np.mean(lat_spacing):.4f} (min: {np.min(lat_spacing):.4f}, max: {np.max(lat_spacing):.4f})")
print(f"Lon spacing: {np.mean(lon_spacing):.4f} (min: {np.min(lon_spacing):.4f}, max: {np.max(lon_spacing):.4f})")

# 3. Temporal Integrity
timestamps = pd.to_datetime(df['timestamp'])
unique_times = np.sort(timestamps.unique())
print(f"Unique timestamps: {len(unique_times)}")
if len(unique_times) > 1:
    time_diffs = np.diff(unique_times).astype('timedelta64[h]')
    print(f"Time steps: avg={np.mean(time_diffs)}, min={np.min(time_diffs)}, max={np.max(time_diffs)}")

# 4. MPS Smoke Test
print("\n--- MPS SMOKE TEST ---")
print(f"PyTorch version: {torch.__version__}")
mps_available = torch.backends.mps.is_available()
print(f"MPS available: {mps_available}")

class DummyConvLSTM(nn.Module):
    def __init__(self, in_channels, hidden_channels):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, hidden_channels, 3, padding=1)
    def forward(self, x):
        # x: [B, T, C, H, W]
        b, t, c, h, w = x.shape
        x_reshaped = x.view(b * t, c, h, w)
        out = self.conv(x_reshaped)
        return out.view(b, t, -1, h, w)

device = torch.device("mps" if mps_available else "cpu")
model = DummyConvLSTM(in_channels=5, hidden_channels=16).to(device)
dummy_tensor = torch.randn(2, 4, 5, 32, 32).to(device) # B=2, T=4, C=5, H=32, W=32
out = model(dummy_tensor)
loss = out.sum()
loss.backward()
print("MPS Forward and Backward pass successful.")

# 5. Memory Estimation
mem = psutil.virtual_memory()
print(f"\n--- MEMORY ESTIMATE ---")
print(f"Total RAM: {mem.total / 1e9:.2f} GB")
print(f"Available RAM: {mem.available / 1e9:.2f} GB")
batch_size = 16
seq_len = 8
channels = 17
tensor_size_mb = (batch_size * seq_len * channels * H * W * 4) / 1e6
print(f"Single batch tensor size: {tensor_size_mb:.2f} MB")
if tensor_size_mb * 5 > mem.available / 1e6:
    print("WARNING: Batch size may cause OOM.")
else:
    print("Memory appears sufficient for batch generator.")

# 6. Tensor Round Trip & Visual Validation
print("\n--- ROUND TRIP & VISUAL ---")
# Pick one timestamp
t0 = unique_times[0]
df_t0 = df[timestamps == t0]

# Map to grid
grid_sic = np.full((H, W), np.nan)
lat_idx = {lat: i for i, lat in enumerate(lats)}
lon_idx = {lon: j for j, lon in enumerate(lons)}

for _, row in df_t0.iterrows():
    i = lat_idx[row['latitude']]
    j = lon_idx[row['longitude']]
    grid_sic[i, j] = row.get('sea_ice_concentration', np.nan)

print(f"Grid SIC populated. NaN count: {np.isnan(grid_sic).sum()} out of {H*W}")

plt.figure(figsize=(8,6))
plt.imshow(grid_sic, origin='lower', extent=[lons.min(), lons.max(), lats.min(), lats.max()])
plt.colorbar(label='Sea Ice Concentration')
plt.title(f"Sea Ice Grid Reconstructed - {t0}")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.savefig("ml/evaluation/convlstm_preflight_sic.png")
print("Saved visual validation to ml/evaluation/convlstm_preflight_sic.png")

# Verify round trip
sample = df_t0.iloc[0]
val = grid_sic[lat_idx[sample['latitude']], lon_idx[sample['longitude']]]
print(f"Round trip check: original={sample.get('sea_ice_concentration')}, tensor={val}")
