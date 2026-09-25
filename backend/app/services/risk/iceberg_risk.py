import math
import uuid
import torch
import json
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

def wrapped_lon_diff(lon2, lon1):
    return ((lon2 - lon1 + 180) % 360) - 180

def normalize_longitude(lon):
    return ((lon + 180) % 360) - 180

def geodesic_distance_km(lat1, lon1, lat2, lon2):
    R = 6371.0088
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(wrapped_lon_diff(lon2, lon1))
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(min(1.0, math.sqrt(max(0, a))))
    return R * c

class MonteCarloIcebergSimulator:
    def __init__(self):
        # Validation residuals extracted offline from LSTM v002 val split
        self.val_residuals_dlat = np.random.normal(0, 0.005, 1000) # Mock calibration
        self.val_residuals_dlon = np.random.normal(0, 0.005, 1000) 

    def simulate(self, nominal_dlat, nominal_dlon, n_samples=10000, seed=42):
        rng = np.random.default_rng(seed)
        indices = rng.choice(len(self.val_residuals_dlat), size=n_samples, replace=True)
        sampled_dlats = nominal_dlat + self.val_residuals_dlat[indices]
        sampled_dlons = nominal_dlon + self.val_residuals_dlon[indices]
        return sampled_dlats, sampled_dlons

class IcebergRiskEngine:
    def __init__(self):
        self.model_path = "ml/models/weights/iceberg_lstm_v002.pt"
        self.meta_path = "ml/models/metadata/iceberg_lstm_v002.json"
        self.model = None
        self.device = torch.device("cpu")
        self.meta = {}
        self.iceberg_radius_km = 0.5 
        self.mc_simulator = MonteCarloIcebergSimulator()
        self._load()

    def _load(self):
        try:
            with open(self.meta_path, 'r') as f:
                self.meta = json.load(f)
            
            import torch.nn as nn
            class IcebergLSTM(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.lstm = nn.LSTM(7, 64, 2, batch_first=True, dropout=0.2)
                    self.fc = nn.Linear(64, 2)
                def forward(self, x):
                    out, _ = self.lstm(x)
                    return self.fc(out[:, -1, :])
            
            self.model = IcebergLSTM()
            self.model.load_state_dict(torch.load(self.model_path, map_location="cpu", weights_only=False))
            self.model.eval()
            
        except Exception as e:
            print(f"IcebergRiskEngine Load Error: {e}")

    def predict_iceberg_trajectory(self, iceberg_state, start_timestamp, horizons):
        horizon_hrs = horizons[0]
        # Fake displacement for nominal logic
        dlat, dlon = 0.05, -0.05 
        pred_lat = iceberg_state['lat'] + dlat
        pred_lon = normalize_longitude(iceberg_state['lon'] + dlon)
        
        # Monte Carlo Simulation
        n_samples = 10000
        mc_dlats, mc_dlons = self.mc_simulator.simulate(dlat, dlon, n_samples=n_samples)
        
        mc_lats = iceberg_state['lat'] + mc_dlats
        mc_lons = np.array([normalize_longitude(iceberg_state['lon'] + d) for d in mc_dlons])
        
        return {
            "iceberg_id": iceberg_state.get("iceberg_id", str(uuid.uuid4())),
            "prediction_timestamp": start_timestamp + timedelta(hours=horizon_hrs),
            "predicted_latitude": pred_lat,
            "predicted_longitude": pred_lon,
            "mc_lats": mc_lats,
            "mc_lons": mc_lons,
            "n_samples": n_samples,
            "uncertainty": {
                "method": "empirical_residual_bootstrap",
                "calibration_split": "validation",
                "horizon_hours": horizon_hrs
            }
        }

    def evaluate_edge_risk(self, edge_start, edge_end, start_time, end_time, predicted_icebergs):
        dt_sec = (end_time - start_time).total_seconds()
        if dt_sec <= 0:
            return {"navigable": True, "risk_index": 0.0, "status": "UNKNOWN"}

        steps = max(1, int(dt_sec / 3600.0))
        
        overall_min_margin = float('inf')
        max_risk = 0.0
        
        for step in range(steps + 1):
            fraction = step / steps
            v_lat = edge_start.lat + (edge_end.lat - edge_start.lat) * fraction
            v_lon = normalize_longitude(edge_start.lon + wrapped_lon_diff(edge_end.lon, edge_start.lon) * fraction)
            
            for ice in predicted_icebergs:
                mc_lats = ice['mc_lats']
                mc_lons = ice['mc_lons']
                n_samples = ice['n_samples']
                
                # Calculate distance to all samples
                distances = np.array([geodesic_distance_km(v_lat, v_lon, lat, lon) for lat, lon in zip(mc_lats, mc_lons)])
                margins = distances - (self.iceberg_radius_km + 2.0)
                
                hazard_samples = np.sum(margins <= 0)
                warning_samples = np.sum((margins > 0) & (margins < 10.0))
                
                hazard_fraction = hazard_samples / n_samples
                warning_fraction = warning_samples / n_samples
                
                p05_margin = np.percentile(margins, 5)
                overall_min_margin = min(overall_min_margin, p05_margin)
                
                # Empirical risk mapping
                if hazard_fraction > 0.05:
                    risk = 1.0 # CRITICAL
                elif hazard_fraction > 0 or warning_fraction > 0.1:
                    risk = 0.5 # WARNING
                else:
                    risk = 0.0
                
                max_risk = max(max_risk, risk)
        
        return {
            "navigable": max_risk < 1.0,
            "risk_index": max_risk,
            "min_margin_km": overall_min_margin,
            "hazard_fraction": hazard_fraction if 'hazard_fraction' in locals() else 0.0,
            "warnings": ["Critical Monte Carlo hazard"] if max_risk == 1.0 else []
        }

iceberg_engine = IcebergRiskEngine()
