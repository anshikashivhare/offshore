"""
Converts the long-format sea-ice DataFrame into a (time, rows, cols)
numpy array — the shape a ConvLSTM needs.
"""
import numpy as np
import pandas as pd


def dataframe_to_grid_sequence(df: pd.DataFrame) -> np.ndarray:
    dates = sorted(df["date"].unique())
    rows = df["row"].max() + 1
    cols = df["col"].max() + 1

    grid_seq = np.zeros((len(dates), rows, cols), dtype=np.float32)
    date_to_idx = {d: i for i, d in enumerate(dates)}

    for _, r in df.iterrows():
        t = date_to_idx[r["date"]]
        grid_seq[t, int(r["row"]), int(r["col"])] = r["concentration"]

    return grid_seq


def make_sequences(grid_seq: np.ndarray, input_len: int = 5):
    """X = input_len consecutive grids, y = the grid immediately after."""
    X, y = [], []
    for t in range(len(grid_seq) - input_len):
        X.append(grid_seq[t : t + input_len])
        y.append(grid_seq[t + input_len])
    return np.stack(X), np.stack(y)
