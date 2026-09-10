"""
Trains a baseline model to predict an iceberg's next-step position
delta (delta-lat, delta-lon) from its current position + environmental
features (ocean current, wind).

Run: python -m ml.training.trajectory_train
"""

import sys
import numpy as np
import pandas as pd
import joblib
from sklearn.multioutput import MultiOutputRegressor
from sklearn.metrics import mean_squared_error
from xgboost import XGBRegressor

from ml.preprocessing.trajectory.data import generate_synthetic_tracks

FEATURE_COLS = ["lat", "lon", "current_u", "current_v", "wind_u", "wind_v"]
TARGET_COLS = ["next_delta_lat", "next_delta_lon"]


def time_based_split_per_iceberg(df, test_frac=0.2):
    train_frames, test_frames = [], []
    for _, group in df.groupby("iceberg_id"):
        cutoff = int(len(group) * (1 - test_frac))
        train_frames.append(group.iloc[:cutoff])
        test_frames.append(group.iloc[cutoff:])
    return pd.concat(train_frames), pd.concat(test_frames)


def train_model(tracks_csv: str = None, reanalysis_nc: str = None):
    if tracks_csv and reanalysis_nc:
        print(f"Loading real data from {tracks_csv} + {reanalysis_nc}...")
        from ml.preprocessing.trajectory.real_data_loader import load_track_csv, merge_tracks_with_environment
        tracks = load_track_csv(tracks_csv)
        df = merge_tracks_with_environment(tracks, reanalysis_nc)
    else:
        print("Generating synthetic data...")
        df = generate_synthetic_tracks()

    train, test = time_based_split_per_iceberg(df)
    print(f"Train rows: {len(train)}, Test rows: {len(test)}")

    X_train, y_train = train[FEATURE_COLS], train[TARGET_COLS]
    X_test, y_test = test[FEATURE_COLS], test[TARGET_COLS]

    base_model = XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
    )
    model = MultiOutputRegressor(base_model)

    print("Training...")
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    rmse_lat = np.sqrt(mean_squared_error(y_test["next_delta_lat"], preds[:, 0]))
    rmse_lon = np.sqrt(mean_squared_error(y_test["next_delta_lon"], preds[:, 1]))
    print(f"Test RMSE — delta_lat: {rmse_lat:.5f}, delta_lon: {rmse_lon:.5f}")

    naive_rmse_lat = np.sqrt(mean_squared_error(y_test["next_delta_lat"], np.zeros(len(y_test))))
    naive_rmse_lon = np.sqrt(mean_squared_error(y_test["next_delta_lon"], np.zeros(len(y_test))))
    print(f"Naive (zero-movement) RMSE — delta_lat: {naive_rmse_lat:.5f}, delta_lon: {naive_rmse_lon:.5f}")

    joblib.dump(model, "ml/trajectory_model/trajectory_model.joblib")
    print("Model saved to ml/trajectory_model/trajectory_model.joblib")

    from mlops.experiment_log import log_experiment
    log_experiment(
        model_name="trajectory_xgboost",
        data_source=f"{tracks_csv}+{reanalysis_nc}" if tracks_csv else "synthetic",
        metrics={
            "rmse_lat": float(rmse_lat), "rmse_lon": float(rmse_lon),
            "naive_rmse_lat": float(naive_rmse_lat), "naive_rmse_lon": float(naive_rmse_lon),
        },
        hyperparams={"n_estimators": 200, "max_depth": 4, "learning_rate": 0.05},
    )

    return model


if __name__ == "__main__":
    tracks_csv = sys.argv[1] if len(sys.argv) > 1 else None
    reanalysis_nc = sys.argv[2] if len(sys.argv) > 2 else None
    train_model(tracks_csv, reanalysis_nc)
