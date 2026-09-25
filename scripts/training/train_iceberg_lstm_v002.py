import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
from torch.utils.data import Dataset, DataLoader
import math

# Configuration
CSV_PATH = "ml/data/raw/iceberg_trajectory_synthetic_2026.csv"
MODEL_PATH = "ml/models/weights/iceberg_lstm_v002.pt"
METRICS_PATH = "ml/evaluation/iceberg_lstm_v002_metrics.json"
METADATA_PATH = "ml/models/metadata/iceberg_lstm_v002.json"
SEQ_LEN = 8
BATCH_SIZE = 128
EPOCHS = 10
LR = 1e-3

print("Loading dataset...")
df = pd.read_csv(CSV_PATH)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values(by=['iceberg_id', 'timestamp'])

# Antimeridian safe longitude difference
def wrapped_lon_diff(lon2, lon1):
    return ((lon2 - lon1 + 180) % 360) - 180

def haversine_dist(lat1, lon1, lat2, lon2):
    R = 6371.0 # km
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(wrapped_lon_diff(lon2, lon1))
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    return R * c

# Prepare features
features = []
targets_lat = []
targets_lon = []

# We will use displacement as input features to prevent absolute coordinate issues
df['d_lat'] = df.groupby('iceberg_id')['latitude_t'].diff()
df['d_lon'] = df.groupby('iceberg_id').apply(lambda x: wrapped_lon_diff(x['longitude_t'], x['longitude_t'].shift(1)), include_groups=False).reset_index(level=0, drop=True)
df['d_lat'] = df['d_lat'].fillna(0)
df['d_lon'] = df['d_lon'].fillna(0)

# Env features
env_cols = ['wind_speed_m_s', 'wind_direction_deg', 'ocean_current_u_m_s', 'ocean_current_v_m_s', 'sea_ice_concentration']
for c in env_cols:
    df[c] = df[c].fillna(0)

feature_cols = ['d_lat', 'd_lon'] + env_cols

# Split icebergs
iceberg_ids = df['iceberg_id'].unique()
np.random.seed(42)
np.random.shuffle(iceberg_ids)

train_ids = iceberg_ids[:22]
val_ids = iceberg_ids[22:26]
test_ids = iceberg_ids[26:30]

print(f"Train icebergs: {len(train_ids)}, Val: {len(val_ids)}, Test: {len(test_ids)}")

# Normalization based on train
train_df = df[df['iceberg_id'].isin(train_ids)]
mean_vals = train_df[feature_cols].mean().values
std_vals = train_df[feature_cols].std().values
std_vals[std_vals == 0] = 1.0

class IcebergDataset(Dataset):
    def __init__(self, data_df, ids):
        self.sequences = []
        self.targets = []
        self.baselines_persist = []
        self.baselines_const_v = []
        self.meta = []
        
        for iid in ids:
            idf = data_df[data_df['iceberg_id'] == iid].copy()
            idf = idf.sort_values('timestamp')
            
            # Normalize features
            feat_data = (idf[feature_cols].values - mean_vals) / std_vals
            
            # Target is the next displacement
            t_dlat = idf['d_lat'].values
            t_dlon = idf['d_lon'].values
            
            # Absolute for evaluation
            abs_lat = idf['latitude_t'].values
            abs_lon = idf['longitude_t'].values
            
            for i in range(SEQ_LEN, len(idf) - 1): # predict i+1
                seq = feat_data[i-SEQ_LEN+1 : i+1]
                target = np.array([t_dlat[i+1], t_dlon[i+1]], dtype=np.float32)
                
                self.sequences.append(seq)
                self.targets.append(target)
                
                # Persistence: displacement = 0
                self.baselines_persist.append(np.array([0.0, 0.0], dtype=np.float32))
                # Const Velocity: displacement = last displacement
                self.baselines_const_v.append(np.array([t_dlat[i], t_dlon[i]], dtype=np.float32))
                
                # Meta for haversine
                self.meta.append((abs_lat[i], abs_lon[i], abs_lat[i+1], abs_lon[i+1]))

    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return (torch.tensor(self.sequences[idx], dtype=torch.float32),
                torch.tensor(self.targets[idx], dtype=torch.float32),
                torch.tensor(self.baselines_persist[idx], dtype=torch.float32),
                torch.tensor(self.baselines_const_v[idx], dtype=torch.float32),
                self.meta[idx])

train_ds = IcebergDataset(df, train_ids)
val_ds = IcebergDataset(df, val_ids)
test_ds = IcebergDataset(df, test_ids)

train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)
test_loader = DataLoader(test_ds, batch_size=BATCH_SIZE, shuffle=False)

print(f"Train sequences: {len(train_ds)}, Val: {len(val_ds)}, Test: {len(test_ds)}")

# Model
class IcebergLSTM(nn.Module):
    def __init__(self, input_dim, hidden_dim, layers, output_dim):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, layers, batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_dim, output_dim)
        
    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :]) # Take last step
        return out

model = IcebergLSTM(input_dim=len(feature_cols), hidden_dim=64, layers=2, output_dim=2)
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
model.to(device)

criterion = nn.MSELoss()
optimizer = optim.AdamW(model.parameters(), lr=LR)

# Antimeridian test function
def test_antimeridian():
    print("\n--- ANTIMERIDIAN TESTS ---")
    print(f"179.9 to -179.9: wrapped diff = {wrapped_lon_diff(-179.9, 179.9):.2f} (expected: 0.20)")
    print(f"-179.9 to 179.9: wrapped diff = {wrapped_lon_diff(179.9, -179.9):.2f} (expected: -0.20)")
    print(f"179.0 to -179.0: wrapped diff = {wrapped_lon_diff(-179.0, 179.0):.2f} (expected: 2.00)")

test_antimeridian()

print("\n--- TRAINING ---")
best_val_loss = float('inf')

for epoch in range(EPOCHS):
    model.train()
    train_loss = 0
    for x, y, _, _, _ in train_loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        preds = model(x)
        loss = criterion(preds, y)
        loss.backward()
        optimizer.step()
        train_loss += loss.item() * x.size(0)
    train_loss /= len(train_ds)
    
    model.eval()
    val_loss = 0
    with torch.no_grad():
        for x, y, _, _, _ in val_loader:
            x, y = x.to(device), y.to(device)
            preds = model(x)
            val_loss += criterion(preds, y).item() * x.size(0)
    val_loss /= len(val_ds)
    
    print(f"Epoch {epoch+1}/{EPOCHS} | Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f}")
    
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        torch.save(model.state_dict(), MODEL_PATH)

print("Saved best model.")

print("\n--- TEST EVALUATION ---")
model.load_state_dict(torch.load(MODEL_PATH))
model.eval()

test_preds = []
test_actuals = []
pers_preds = []
const_preds = []
test_meta = []

with torch.no_grad():
    for x, y, p, c, meta in test_loader:
        x = x.to(device)
        preds = model(x).cpu().numpy()
        test_preds.extend(preds)
        test_actuals.extend(y.numpy())
        pers_preds.extend(p.numpy())
        const_preds.extend(c.numpy())
        
        # meta is a tuple of tuples: (lat0, lon0, lat1, lon1)
        # We need to transpose to get list of (lat0, lon0, lat1, lon1)
        for i in range(len(meta[0])):
            test_meta.append((meta[0][i].item(), meta[1][i].item(), meta[2][i].item(), meta[3][i].item()))

test_preds = np.array(test_preds)
test_actuals = np.array(test_actuals)
pers_preds = np.array(pers_preds)
const_preds = np.array(const_preds)

def evaluate_errors(preds, actuals, meta, name):
    maes = np.abs(preds - actuals).mean(axis=0)
    
    hav_errors = []
    for i in range(len(preds)):
        lat0, lon0, lat1, lon1 = meta[i] # actual origin and target absolute coords
        pred_dlat = preds[i][0]
        pred_dlon = preds[i][1]
        
        # reconstruct pred absolute
        pred_lat = lat0 + pred_dlat
        pred_lon = (lon0 + pred_dlon + 180) % 360 - 180
        
        err = haversine_dist(lat1, lon1, pred_lat, pred_lon)
        hav_errors.append(err)
        
    mean_hav = np.mean(hav_errors)
    print(f"[{name}] MAE (dLat, dLon): {maes[0]:.6f}, {maes[1]:.6f} | Mean Haversine Error: {mean_hav:.2f} km")
    return {"mae_dlat": float(maes[0]), "mae_dlon": float(maes[1]), "mean_haversine_km": float(mean_hav)}

res_model = evaluate_errors(test_preds, test_actuals, test_meta, "LSTM v002")
res_pers = evaluate_errors(pers_preds, test_actuals, test_meta, "Persistence")
res_const = evaluate_errors(const_preds, test_actuals, test_meta, "Constant Velocity")

# Save metrics
metrics = {
    "test_samples": len(test_ds),
    "model": res_model,
    "persistence": res_pers,
    "constant_velocity": res_const
}
with open(METRICS_PATH, 'w') as f:
    json.dump(metrics, f, indent=2)

# Save metadata
metadata = {
    "artifact_version": "v002",
    "architecture": "LSTM",
    "sequence_length": SEQ_LEN,
    "features": feature_cols,
    "target": ["delta_latitude", "wrapped_delta_longitude"],
    "normalization_mean": mean_vals.tolist(),
    "normalization_std": std_vals.tolist(),
    "train_icebergs": int(len(train_ids)),
    "val_icebergs": int(len(val_ids)),
    "test_icebergs": int(len(test_ids)),
    "synthetic_or_real": "SYNTHETIC",
    "baseline_comparison": metrics
}
os.makedirs(os.path.dirname(METADATA_PATH), exist_ok=True)
with open(METADATA_PATH, 'w') as f:
    json.dump(metadata, f, indent=2)

print("Training script completed successfully.")
