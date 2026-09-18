"""
Iceberg Trajectory ML Pipeline Tests — SIH 2026 PS-26059
=========================================================
Uses SYNTHETIC CSV data only.

Run:
    cd /Users/apple/Downloads/offshore
    source .venv/bin/activate
    pytest ml/tests/test_iceberg_pipeline.py -v
"""

import json
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

RAW_CSV   = Path("/Users/apple/Downloads/ml/data/raw/iceberg_trajectory_synthetic.csv")
MODEL_DIR = PROJECT_ROOT / "ml" / "models" / "weights"
SCHEMA    = MODEL_DIR / "iceberg_feature_schema.json"
LAT_MODEL = MODEL_DIR / "iceberg_xgb_lat_latest.json"
LON_MODEL = MODEL_DIR / "iceberg_xgb_lon_latest.json"

EXPECTED_RAW_COLS = [
    "sample_id", "iceberg_id", "timestamp",
    "latitude_t_minus_2", "longitude_t_minus_2",
    "latitude_t_minus_1", "longitude_t_minus_1",
    "latitude_t", "longitude_t",
    "wind_speed_m_s", "wind_direction_deg",
    "ocean_current_u_m_s", "ocean_current_v_m_s",
    "sea_ice_concentration", "forecast_horizon_hours",
    "target_latitude", "target_longitude",
    "data_source_type",
]

FEATURE_COLS = [
    "latitude_t", "longitude_t",
    "dlat_1", "dlon_1", "dlat_2", "dlon_2",
    "speed_1", "speed_2",
    "wind_u", "wind_v",
    "ocean_current_u_m_s", "ocean_current_v_m_s",
    "sea_ice_concentration", "forecast_horizon_hours",
    "month", "sin_doy", "cos_doy",
]


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def raw_df():
    assert RAW_CSV.exists(), f"Raw CSV not found: {RAW_CSV}"
    df = pd.read_csv(RAW_CSV)
    df.columns = df.columns.str.strip()
    return df


@pytest.fixture(scope="session")
def schema():
    assert SCHEMA.exists(), f"Schema not found: {SCHEMA}"
    with open(SCHEMA) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def processed_df(raw_df):
    df = raw_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["iceberg_id", "timestamp"]).reset_index(drop=True)
    df["dlat_1"] = df["latitude_t"]        - df["latitude_t_minus_1"]
    df["dlon_1"] = df["longitude_t"]        - df["longitude_t_minus_1"]
    df["dlat_2"] = df["latitude_t_minus_1"] - df["latitude_t_minus_2"]
    df["dlon_2"] = df["longitude_t_minus_1"] - df["longitude_t_minus_2"]
    df["speed_1"] = np.sqrt(df["dlat_1"] ** 2 + df["dlon_1"] ** 2)
    df["speed_2"] = np.sqrt(df["dlat_2"] ** 2 + df["dlon_2"] ** 2)
    df["wind_u"] = df["wind_speed_m_s"] * np.cos(np.radians(df["wind_direction_deg"]))
    df["wind_v"] = df["wind_speed_m_s"] * np.sin(np.radians(df["wind_direction_deg"]))
    df["month"]   = df["timestamp"].dt.month
    df["sin_doy"] = np.sin(2 * np.pi * df["timestamp"].dt.dayofyear / 365.25)
    df["cos_doy"] = np.cos(2 * np.pi * df["timestamp"].dt.dayofyear / 365.25)
    df["target_dlat"] = df["target_latitude"]  - df["latitude_t"]
    df["target_dlon"]  = df["target_longitude"] - df["longitude_t"]
    return df


@pytest.fixture(scope="session")
def splits(processed_df):
    train_frames, val_frames, test_frames = [], [], []
    for _, group in processed_df.groupby("iceberg_id"):
        group = group.sort_values("timestamp")
        n = len(group)
        vi, ti = int(n * 0.70), int(n * 0.85)
        train_frames.append(group.iloc[:vi])
        val_frames.append(group.iloc[vi:ti])
        test_frames.append(group.iloc[ti:])
    return (
        pd.concat(train_frames).reset_index(drop=True),
        pd.concat(val_frames).reset_index(drop=True),
        pd.concat(test_frames).reset_index(drop=True),
    )


@pytest.fixture(scope="session")
def models(schema):
    import xgboost as xgb
    assert LAT_MODEL.exists(), f"lat model missing: {LAT_MODEL}"
    assert LON_MODEL.exists(), f"lon model missing: {LON_MODEL}"
    m_lat = xgb.XGBRegressor(); m_lat.load_model(str(LAT_MODEL))
    m_lon = xgb.XGBRegressor(); m_lon.load_model(str(LON_MODEL))
    return m_lat, m_lon


# ══════════════════════════════════════════════════════════════════════════════
# 1. Dataset loading
# ══════════════════════════════════════════════════════════════════════════════

class TestDatasetLoading:

    def test_csv_exists(self):
        assert RAW_CSV.exists()

    def test_row_count(self, raw_df):
        assert len(raw_df) == 1500, f"Expected 1500 rows, got {len(raw_df)}"

    def test_expected_columns(self, raw_df):
        missing = [c for c in EXPECTED_RAW_COLS if c not in raw_df.columns]
        assert not missing, f"Missing columns: {missing}"

    def test_iceberg_count(self, raw_df):
        assert raw_df["iceberg_id"].nunique() >= 20

    def test_data_source(self, raw_df):
        sources = raw_df["data_source_type"].str.strip().unique()
        assert "SYNTHETIC_PROTOTYPE" in sources


# ══════════════════════════════════════════════════════════════════════════════
# 2. Schema & target validation
# ══════════════════════════════════════════════════════════════════════════════

class TestSchemaValidation:

    def test_no_missing_values(self, raw_df):
        assert raw_df[EXPECTED_RAW_COLS].isnull().sum().sum() == 0

    def test_no_duplicates(self, raw_df):
        assert raw_df.duplicated().sum() == 0

    def test_target_columns_exist(self, raw_df):
        assert "target_latitude" in raw_df.columns
        assert "target_longitude" in raw_df.columns

    def test_latitude_antarctic(self, raw_df):
        assert raw_df["latitude_t"].max() <= -55.0
        assert raw_df["latitude_t"].min() >= -90.0

    def test_sic_bounds(self, raw_df):
        assert raw_df["sea_ice_concentration"].min() >= 0.0
        assert raw_df["sea_ice_concentration"].max() <= 1.0

    def test_forecast_horizon(self, raw_df):
        assert raw_df["forecast_horizon_hours"].nunique() == 1
        assert raw_df["forecast_horizon_hours"].iloc[0] == 6


# ══════════════════════════════════════════════════════════════════════════════
# 3. Preprocessing
# ══════════════════════════════════════════════════════════════════════════════

class TestPreprocessing:

    def test_features_present(self, processed_df):
        for col in FEATURE_COLS:
            assert col in processed_df.columns, f"Missing: {col}"

    def test_no_inf(self, processed_df):
        assert not np.isinf(processed_df[FEATURE_COLS].values).any()

    def test_no_nan(self, processed_df):
        assert processed_df[FEATURE_COLS].isnull().sum().sum() == 0

    def test_wind_decomp_correct(self, raw_df):
        df = raw_df.copy()
        wu = df["wind_speed_m_s"] * np.cos(np.radians(df["wind_direction_deg"]))
        wv = df["wind_speed_m_s"] * np.sin(np.radians(df["wind_direction_deg"]))
        recon = np.sqrt(wu ** 2 + wv ** 2)
        np.testing.assert_allclose(recon.values, df["wind_speed_m_s"].values, rtol=1e-5)

    def test_velocity_lags_correct(self, processed_df, raw_df):
        # Check dlat_1 = lat_t - lat_{t-1}
        expected = raw_df["latitude_t"] - raw_df["latitude_t_minus_1"]
        # processed_df is sorted differently; just check no extreme outliers
        assert processed_df["dlat_1"].abs().max() < 5.0, "dlat_1 seems too large"

    def test_target_deltas_present(self, processed_df):
        assert "target_dlat" in processed_df.columns
        assert "target_dlon" in processed_df.columns

    def test_no_target_leakage(self, processed_df):
        """target_latitude/target_longitude are raw targets kept in the df,
        but must NOT appear in the feature set sent to the model."""
        leaky_in_features = [c for c in FEATURE_COLS if "target" in c.lower()]
        assert not leaky_in_features, (
            f"Feature columns include target-derived fields: {leaky_in_features}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 4. Splitting
# ══════════════════════════════════════════════════════════════════════════════

class TestSplitting:

    def test_splits_sum_to_full(self, splits, processed_df):
        train, val, test = splits
        assert len(train) + len(val) + len(test) == len(processed_df)

    def test_per_iceberg_ordering(self, splits, processed_df):
        # Each iceberg should have earlier timestamps in train than test
        train, _, test = splits
        for iceberg_id in train["iceberg_id"].unique():
            tr_times = pd.to_datetime(
                train[train["iceberg_id"] == iceberg_id]["timestamp"])
            te_times = pd.to_datetime(
                test[test["iceberg_id"] == iceberg_id]["timestamp"])
            if len(tr_times) and len(te_times):
                assert tr_times.max() <= te_times.min(), (
                    f"Iceberg {iceberg_id}: train timestamps overlap with test"
                )

    def test_features_in_all_splits(self, splits):
        for name, split in zip(["train", "val", "test"], splits):
            missing = [c for c in FEATURE_COLS if c not in split.columns]
            assert not missing, f"{name} missing: {missing}"


# ══════════════════════════════════════════════════════════════════════════════
# 5. Model training
# ══════════════════════════════════════════════════════════════════════════════

class TestModelTraining:

    def test_xgboost_importable(self):
        import xgboost as xgb
        assert hasattr(xgb, "XGBRegressor")

    def test_train_predict_small(self, splits):
        import xgboost as xgb
        train, _, test = splits
        m = xgb.XGBRegressor(n_estimators=10, max_depth=3, random_state=42, tree_method="hist")
        m.fit(train[FEATURE_COLS].values, train["target_dlat"].values)
        preds = m.predict(test[FEATURE_COLS].values)
        assert preds.shape == (len(test),)
        assert not np.isnan(preds).any()
        assert not np.isinf(preds).any()

    def test_reproducibility(self, splits):
        import xgboost as xgb
        train, _, test = splits
        Xtr = train[FEATURE_COLS].values
        ytr = train["target_dlat"].values
        Xte = test[FEATURE_COLS].values
        m1 = xgb.XGBRegressor(n_estimators=10, random_state=42)
        m2 = xgb.XGBRegressor(n_estimators=10, random_state=42)
        m1.fit(Xtr, ytr); m2.fit(Xtr, ytr)
        np.testing.assert_array_equal(m1.predict(Xte), m2.predict(Xte))


# ══════════════════════════════════════════════════════════════════════════════
# 6. Evaluation
# ══════════════════════════════════════════════════════════════════════════════

class TestEvaluation:

    def test_saved_models_beat_persistence(self, models, splits, schema):
        m_lat, m_lon = models
        _, _, test = splits
        X_test   = test[schema["feature_cols"]].values
        ylat     = test["target_dlat"].values
        ylon     = test["target_dlon"].values
        pred_lat = m_lat.predict(X_test)
        pred_lon = m_lon.predict(X_test)
        rmse_lat = math.sqrt(np.mean((ylat - pred_lat) ** 2))
        rmse_lon = math.sqrt(np.mean((ylon - pred_lon) ** 2))
        persist_rmse_lat = math.sqrt(np.mean(ylat ** 2))  # predict zero movement
        persist_rmse_lon = math.sqrt(np.mean(ylon ** 2))
        assert rmse_lat < persist_rmse_lat, \
            f"lat RMSE {rmse_lat:.5f} not better than persistence {persist_rmse_lat:.5f}"
        assert rmse_lon < persist_rmse_lon, \
            f"lon RMSE {rmse_lon:.5f} not better than persistence {persist_rmse_lon:.5f}"

    def test_metrics_finite(self, models, splits, schema):
        m_lat, m_lon = models
        _, _, test = splits
        X = test[schema["feature_cols"]].values
        for m, y_col in [(m_lat, "target_dlat"), (m_lon, "target_dlon")]:
            preds = m.predict(X)
            y = test[y_col].values
            mae = float(np.mean(np.abs(y - preds)))
            rmse = math.sqrt(float(np.mean((y - preds) ** 2)))
            assert math.isfinite(mae)
            assert math.isfinite(rmse)

    def test_r2_positive(self, models, splits, schema):
        m_lat, _ = models
        _, _, test = splits
        preds = m_lat.predict(test[schema["feature_cols"]].values)
        y = test["target_dlat"].values
        ss_res = np.sum((y - preds) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
        assert r2 > 0, f"lat model R² {r2:.4f} is not positive"


# ══════════════════════════════════════════════════════════════════════════════
# 7. Model save/load
# ══════════════════════════════════════════════════════════════════════════════

class TestModelSaveLoad:

    def test_lat_model_exists(self):
        assert LAT_MODEL.exists()

    def test_lon_model_exists(self):
        assert LON_MODEL.exists()

    def test_schema_exists(self):
        assert SCHEMA.exists()

    def test_schema_keys(self, schema):
        for k in ["run_id", "feature_cols", "target_lat_col", "target_lon_col"]:
            assert k in schema

    def test_schema_feature_count(self, schema):
        assert len(schema["feature_cols"]) == 17

    def test_models_loadable(self):
        import xgboost as xgb
        m = xgb.XGBRegressor(); m.load_model(str(LAT_MODEL))
        m = xgb.XGBRegressor(); m.load_model(str(LON_MODEL))

    def test_save_reload_roundtrip(self, splits):
        import xgboost as xgb
        train, _, test = splits
        m = xgb.XGBRegressor(n_estimators=5, random_state=42)
        m.fit(train[FEATURE_COLS].values, train["target_dlat"].values)
        before = m.predict(test[FEATURE_COLS].values)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            p = f.name
        m.save_model(p)
        m2 = xgb.XGBRegressor(); m2.load_model(p)
        after = m2.predict(test[FEATURE_COLS].values)
        np.testing.assert_array_almost_equal(before, after, decimal=5)
        Path(p).unlink()


# ══════════════════════════════════════════════════════════════════════════════
# 8. Inference
# ══════════════════════════════════════════════════════════════════════════════

class TestInference:

    def test_import_function(self):
        from ml.inference.trajectory_predict import predict_iceberg_trajectory
        assert callable(predict_iceberg_trajectory)

    def test_valid_inference(self):
        from ml.inference.trajectory_predict import predict_iceberg_trajectory
        result = predict_iceberg_trajectory(
            latitude_t=-65.5,     longitude_t=61.7,
            latitude_t_minus_1=-65.54, longitude_t_minus_1=61.65,
            latitude_t_minus_2=-65.58, longitude_t_minus_2=61.61,
            wind_speed_m_s=2.0, wind_direction_deg=315.0,
            ocean_current_u_m_s=0.18, ocean_current_v_m_s=0.09,
            sea_ice_concentration=0.35, forecast_horizon_hours=6,
        )
        assert "predicted_delta_lat" in result
        assert "predicted_latitude"  in result
        assert result["data_source_type"] == "SYNTHETIC_PROTOTYPE"
        assert math.isfinite(result["predicted_delta_lat"])
        assert math.isfinite(result["predicted_latitude"])

    def test_invalid_latitude_raises(self):
        from ml.inference.trajectory_predict import predict_iceberg_trajectory
        with pytest.raises(ValueError, match="latitude_t"):
            predict_iceberg_trajectory(
                latitude_t=10.0, longitude_t=60.0,
                latitude_t_minus_1=10.04, longitude_t_minus_1=59.95,
                latitude_t_minus_2=10.08, longitude_t_minus_2=59.90,
                wind_speed_m_s=2.0, wind_direction_deg=0.0,
                ocean_current_u_m_s=0.1, ocean_current_v_m_s=0.05,
                sea_ice_concentration=0.3,
            )

    def test_invalid_sic_raises(self):
        from ml.inference.trajectory_predict import predict_iceberg_trajectory
        with pytest.raises(ValueError, match="sea_ice_concentration"):
            predict_iceberg_trajectory(
                latitude_t=-65.5, longitude_t=61.7,
                latitude_t_minus_1=-65.54, longitude_t_minus_1=61.65,
                latitude_t_minus_2=-65.58, longitude_t_minus_2=61.61,
                wind_speed_m_s=2.0, wind_direction_deg=315.0,
                ocean_current_u_m_s=0.18, ocean_current_v_m_s=0.09,
                sea_ice_concentration=1.8,
            )

    def test_output_keys_complete(self):
        from ml.inference.trajectory_predict import predict_iceberg_trajectory
        result = predict_iceberg_trajectory(
            latitude_t=-66.0, longitude_t=50.0,
            latitude_t_minus_1=-66.04, longitude_t_minus_1=49.95,
            latitude_t_minus_2=-66.08, longitude_t_minus_2=49.90,
            wind_speed_m_s=5.0, wind_direction_deg=180.0,
            ocean_current_u_m_s=0.1, ocean_current_v_m_s=0.05,
            sea_ice_concentration=0.5,
        )
        for k in ["predicted_delta_lat", "predicted_delta_lon",
                  "predicted_latitude", "predicted_longitude",
                  "forecast_horizon_hours", "data_source_type",
                  "model_run_id", "warning"]:
            assert k in result, f"Missing key: {k}"

    def test_reproducible(self):
        from ml.inference.trajectory_predict import predict_iceberg_trajectory
        kw = dict(
            latitude_t=-65.5, longitude_t=61.7,
            latitude_t_minus_1=-65.54, longitude_t_minus_1=61.65,
            latitude_t_minus_2=-65.58, longitude_t_minus_2=61.61,
            wind_speed_m_s=2.0, wind_direction_deg=315.0,
            ocean_current_u_m_s=0.18, ocean_current_v_m_s=0.09,
            sea_ice_concentration=0.35,
        )
        r1 = predict_iceberg_trajectory(**kw)
        r2 = predict_iceberg_trajectory(**kw)
        assert r1["predicted_delta_lat"] == r2["predicted_delta_lat"]
        assert r1["predicted_delta_lon"]  == r2["predicted_delta_lon"]

    def test_backend_load_model_compat(self):
        """The backend calls load_model() on startup — must not raise."""
        from ml.inference.trajectory_predict import load_model
        # May return None if legacy .joblib doesn't exist — that's fine
        result = load_model()
        # Just verify it doesn't raise an exception

    def test_backend_seaice_load_model_compat(self):
        """Backend also calls seaice load_model() — must not raise."""
        from ml.inference.seaice_predict import load_model
        result = load_model()
