import pytest
import pandas as pd
import numpy as np

from ml.benchmarks.metrics import haversine_distance, calculate_trajectory_metrics
from ml.benchmarks.splits import time_based_split_strict, time_based_split_per_entity_strict
from ml.benchmarks.baselines import TrajectoryPersistenceBaseline, SeaIcePersistenceBaseline
from ml.benchmarks.hard_cases import get_trajectory_hard_case_masks

def test_haversine_distance():
    # Test known distance: e.g. 1 degree of latitude is ~111 km
    lat1, lon1 = 0, 0
    lat2, lon2 = 1, 0
    dist = haversine_distance(lat1, lon1, lat2, lon2)
    assert np.isclose(dist, 111.1, atol=0.2)

def test_calculate_trajectory_metrics():
    y_true = [[0.1, 0.1], [0.0, 0.0]]
    y_pred = [[0.1, 0.1], [0.0, 0.0]]
    lats = [0, 1]
    lons = [0, 1]
    
    metrics = calculate_trajectory_metrics(y_true, y_pred, lats, lons)
    assert metrics["mae"] == 0.0
    assert metrics["rmse"] == 0.0
    assert metrics["mean_position_error_km"] == 0.0

def test_time_based_split_strict():
    df = pd.DataFrame({"date": range(100), "val": range(100)})
    train, val, test = time_based_split_strict(df, val_frac=0.15, test_frac=0.15)
    
    assert len(train) in (69, 70, 71)
    assert len(val) in (14, 15, 16)
    assert len(test) in (14, 15, 16)
    
    assert train["date"].max() < val["date"].min()
    assert val["date"].max() < test["date"].min()

def test_time_based_split_per_entity_strict():
    df = pd.DataFrame({
        "iceberg_id": [1]*100 + [2]*100,
        "date": list(range(100)) + list(range(100)),
        "val": range(200)
    })
    
    train, val, test = time_based_split_per_entity_strict(df)
    
    assert len(train) == 140
    assert len(val) == 30
    assert len(test) == 30
    
    # Check iceberg 1 boundary
    train_1 = train[train["iceberg_id"] == 1]
    val_1 = val[val["iceberg_id"] == 1]
    assert train_1["date"].max() < val_1["date"].min()

def test_trajectory_persistence():
    baseline = TrajectoryPersistenceBaseline()
    X = pd.DataFrame({"dummy": range(10)})
    preds = baseline.predict(X)
    assert preds.shape == (10, 2)
    assert np.all(preds == 0)

def test_hard_case_evaluation():
    df = pd.DataFrame({
        "wind_u": [0.0, 0.02, -0.05],
        "wind_v": [0.0, 0.0, 0.0],
        "current_u": [0.0, 0.0, 0.0],
        "current_v": [0.0, 0.0, 0.0]
    })
    masks = get_trajectory_hard_case_masks(df)
    assert "overall" in masks
    assert "strong_wind" in masks
    
    # Rows 1 and 2 should be strong wind
    assert masks["strong_wind"].tolist() == [False, True, True]
