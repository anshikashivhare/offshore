import numpy as np
import pandas as pd

from ml.benchmarks.hard_cases import (get_seaice_hard_case_masks,
                                      get_trajectory_hard_case_masks)
from ml.benchmarks.metrics import (calculate_seaice_metrics,
                                   calculate_trajectory_metrics)


def evaluate_trajectory_model(
    model,
    df: pd.DataFrame,
    feature_cols,
    target_cols,
    lat_col="lat",
    lon_col="lon",
    is_baseline=False,
):
    """
    Evaluates a trajectory model (or baseline) across all defined hard cases.
    df must be the raw, unsequenced test dataframe.
    """
    masks = get_trajectory_hard_case_masks(df)
    results = {}

    # Generate predictions
    if is_baseline:
        preds = model.predict(df[feature_cols])
    else:
        # Assuming scikit-learn/xgboost interface for simple models
        # For sequence models, the caller should adapt the df to sequences,
        # but the masks must align with the targets.
        preds = model.predict(df[feature_cols])

    y_true = df[target_cols].values
    lats = df[lat_col].values
    lons = df[lon_col].values

    for case_name, mask in masks.items():
        if not mask.any():
            continue

        case_y_true = y_true[mask]
        case_preds = preds[mask]
        case_lats = lats[mask]
        case_lons = lons[mask]

        metrics = calculate_trajectory_metrics(
            case_y_true, case_preds, case_lats, case_lons
        )
        results[case_name] = metrics

    return results


def evaluate_seaice_model(
    model, df: pd.DataFrame, feature_cols, target_col, is_baseline=False
):
    masks = get_seaice_hard_case_masks(df)
    results = {}

    if is_baseline:
        preds = model.predict(df["lag_1"])
    else:
        preds = model.predict(df[feature_cols])

    y_true = df[target_col].values

    for case_name, mask in masks.items():
        if not mask.any():
            continue

        case_y_true = y_true[mask]
        case_preds = preds[mask]

        metrics = calculate_seaice_metrics(case_y_true, case_preds)
        results[case_name] = metrics

    return results
