"""
Trains a baseline XGBoost model to forecast next-day sea-ice
concentration per grid cell, using lag features + seasonal features.

Run: python -m ml.training.seaice_train
"""

import sys

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
from xgboost import XGBRegressor

from ml.path_utils import get_model_path
from ml.preprocessing.seaice.data import generate_synthetic_timeseries


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["row", "col", "date"]).copy()
    grp = df.groupby(["row", "col"])["concentration"]

    df["lag_1"] = grp.shift(1)
    df["lag_2"] = grp.shift(2)
    df["lag_3"] = grp.shift(3)
    df["day_of_year"] = df["date"].dt.dayofyear

    df = df.dropna(subset=["lag_1", "lag_2", "lag_3"])
    return df


def time_based_split(df: pd.DataFrame, val_frac=0.15, test_frac=0.15):
    val_cutoff = df["date"].quantile(
        1 - (val_frac + test_frac), interpolation="nearest"
    )
    test_cutoff = df["date"].quantile(1 - test_frac, interpolation="nearest")
    train = df[df["date"] < val_cutoff]
    val = df[(df["date"] >= val_cutoff) & (df["date"] < test_cutoff)]
    test = df[df["date"] >= test_cutoff]
    return train, val, test


FEATURE_COLS = ["lag_1", "lag_2", "lag_3", "day_of_year", "lat", "lon"]
TARGET_COL = "concentration"


def train_model(nc_path: str = None):
    if nc_path:
        print(f"Loading real data from {nc_path}...")
        from ml.preprocessing.seaice.real_data_loader import \
            load_netcdf_to_dataframe

        df = load_netcdf_to_dataframe(nc_path)
    else:
        print("Generating synthetic data...")
        df = generate_synthetic_timeseries()

    print("Building features...")
    df = build_features(df)

    train, val, test = time_based_split(df)
    print(f"Train rows: {len(train)}, Val rows: {len(val)}, Test rows: {len(test)}")

    X_train, y_train = train[FEATURE_COLS], train[TARGET_COL]
    X_val, y_val = val[FEATURE_COLS], val[TARGET_COL]
    X_test, y_test = test[FEATURE_COLS], test[TARGET_COL]

    model = XGBRegressor(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        early_stopping_rounds=30,
    )
    print("Training...")
    model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

    preds = model.predict(X_test)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    print(f"Test RMSE: {rmse:.4f}")

    naive_rmse = np.sqrt(mean_squared_error(y_test, X_test["lag_1"]))
    print(f"Naive (persistence) RMSE: {naive_rmse:.4f}")

    import uuid

    run_id = str(uuid.uuid4())
    artifact_uri = get_model_path(f"seaice_xgb_{run_id}.json")

    model.save_model(artifact_uri)
    print(f"Model saved to {artifact_uri}")

    from mlops.experiment_log import log_experiment

    log_experiment(
        run_id=run_id,
        model_name="seaice_xgboost",
        data_source=nc_path or "synthetic",
        artifact_uri=artifact_uri,
        metrics={"test_rmse": float(rmse), "naive_rmse": float(naive_rmse)},
        hyperparams={
            "n_estimators": 300,
            "max_depth": 5,
            "learning_rate": 0.05,
            "early_stopping_rounds": 30,
        },
    )

    return model, rmse, artifact_uri


if __name__ == "__main__":
    nc_path = sys.argv[1] if len(sys.argv) > 1 else None
    train_model(nc_path)
