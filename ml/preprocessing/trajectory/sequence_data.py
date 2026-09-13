"""
Builds sliding-window sequences from iceberg track data for the LSTM.
"""

import numpy as np
import pandas as pd

FEATURE_COLS = ["lat", "lon", "current_u", "current_v", "wind_u", "wind_v"]


def make_sequences(df: pd.DataFrame, seq_len: int = 5):
    X, y = [], []
    for _, group in df.groupby("iceberg_id"):
        group = group.sort_values("timestep").reset_index(drop=True)
        feats = group[FEATURE_COLS].values
        targets = group[["next_delta_lat", "next_delta_lon"]].values
        for t in range(len(group) - seq_len):
            X.append(feats[t : t + seq_len])
            y.append(targets[t + seq_len - 1])
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)
