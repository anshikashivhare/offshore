import os
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error
from pathlib import Path
import math

# Paths
raw_data_path = Path("ml/data/raw/iceberg_trajectory_synthetic_2026.csv")
model_out_path = Path("ml/models/weights/iceberg_lstm_v001.pt")
metrics_out_path = Path("ml/evaluation/iceberg_lstm_v001_metrics.json")

model_out_path.parent.mkdir(parents=True, exist_ok=True)
metrics_out_path.parent.mkdir(parents=True, exist_ok=True)

# 1. Load Data
df = pd.read_csv(raw_data_path)

# Ensure no missing values
df = df.dropna(subset=['latitude_t_minus_2', 'target_latitude']).copy()

# 2. Split by iceberg_id to prevent leakage
unique_icebergs = df['iceberg_id'].unique()
np.random.seed(42)
np.random.shuffle(unique_icebergs)

n = len(unique_icebergs)
train_ids = unique_icebergs[:int(n * 0.70)]
val_ids = unique_icebergs[int(n * 0.70):int(n * 0.85)]
test_ids = unique_icebergs[int(n * 0.85):]

train_df = df[df['iceberg_id'].isin(train_ids)]
val_df = df[df['iceberg_id'].isin(val_ids)]
test_df = df[df['iceberg_id'].isin(test_ids)]

print(f"Train icebergs: {len(train_ids)}, Val: {len(val_ids)}, Test: {len(test_ids)}")

# 3. PyTorch Dataset
class IcebergDataset(Dataset):
    def __init__(self, data):
        # We construct a sequence of shape (batch, seq_len=3, features=2) for lat/lon
        self.seq_t_minus_2 = data[['latitude_t_minus_2', 'longitude_t_minus_2']].values
        self.seq_t_minus_1 = data[['latitude_t_minus_1', 'longitude_t_minus_1']].values
        self.seq_t = data[['latitude_t', 'longitude_t']].values
        
        self.env = data[['wind_speed_m_s', 'wind_direction_deg', 'ocean_current_u_m_s', 'ocean_current_v_m_s', 'sea_ice_concentration']].values
        self.targets = data[['target_latitude', 'target_longitude']].values
        
    def __len__(self):
        return len(self.targets)
        
    def __getitem__(self, idx):
        # Shape: (3, 2)
        seq = np.vstack([self.seq_t_minus_2[idx], self.seq_t_minus_1[idx], self.seq_t[idx]])
        env = self.env[idx]
        # We append env to each step of the sequence (broadcasting it)
        env_seq = np.tile(env, (3, 1))
        # Concatenate features: (3, 2 + 5) = (3, 7)
        full_seq = np.concatenate([seq, env_seq], axis=1)
        
        return torch.tensor(full_seq, dtype=torch.float32), torch.tensor(self.targets[idx], dtype=torch.float32)

train_loader = DataLoader(IcebergDataset(train_df), batch_size=256, shuffle=True)
val_loader = DataLoader(IcebergDataset(val_df), batch_size=256)
test_loader = DataLoader(IcebergDataset(test_df), batch_size=256)

# 4. LSTM Model
class IcebergLSTM(nn.Module):
    def __init__(self, input_size=7, hidden_size=64, num_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 2) # Predicts lat, lon
        
    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :] # Take last time step
        return self.fc(out)

# 5. Training Loop
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"Using device: {device}")

model = IcebergLSTM().to(device)
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

best_val_loss = float('inf')
epochs = 20

for epoch in range(epochs):
    model.train()
    train_loss = 0
    for X_batch, y_batch in train_loader:
        X_batch, y_batch = X_batch.to(device), y_batch.to(device)
        
        optimizer.zero_grad()
        preds = model(X_batch)
        loss = criterion(preds, y_batch)
        loss.backward()
        optimizer.step()
        train_loss += loss.item()
        
    model.eval()
    val_loss = 0
    with torch.no_grad():
        for X_batch, y_batch in val_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            preds = model(X_batch)
            loss = criterion(preds, y_batch)
            val_loss += loss.item()
            
    train_loss /= len(train_loader)
    val_loss /= len(val_loader)
    print(f"Epoch {epoch+1}/{epochs} - Train MSE: {train_loss:.4f} - Val MSE: {val_loss:.4f}")
    
    if val_loss < best_val_loss:
        best_val_loss = val_loss
        torch.save(model.state_dict(), model_out_path)

# 6. Evaluation on Test Set
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # km
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

model.load_state_dict(torch.load(model_out_path))
model.eval()

all_preds = []
all_targets = []
with torch.no_grad():
    for X_batch, y_batch in test_loader:
        X_batch = X_batch.to(device)
        preds = model(X_batch).cpu().numpy()
        all_preds.append(preds)
        all_targets.append(y_batch.numpy())

all_preds = np.vstack(all_preds)
all_targets = np.vstack(all_targets)

rmse = np.sqrt(mean_squared_error(all_targets, all_preds))
# Calculate average haversine error in km
distances = haversine(all_targets[:, 0], all_targets[:, 1], all_preds[:, 0], all_preds[:, 1])
mean_distance = np.mean(distances)

metrics = {
    "test_rmse": float(rmse),
    "test_mean_haversine_error_km": float(mean_distance)
}

with open(metrics_out_path, 'w') as f:
    json.dump(metrics, f, indent=2)

print("LSTM Training Complete. Metrics:", json.dumps(metrics, indent=2))
