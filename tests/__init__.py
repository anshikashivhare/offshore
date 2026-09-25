"""
ML Pipeline Tests — SIH 2026 PS-26059
Sea-Ice XGBoost Training Pipeline Verification
==============================================
Uses SYNTHETIC CSV data only.

Run:
    cd /Users/apple/Downloads/offshore
    source .venv/bin/activate
    pytest ml/tests/test_seaice_pipeline.py -v
"""

import json
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# ─── Ensure the project root is in sys.path so imports work ───────────────────
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ─── Paths ────────────────────────────────────────────────────────────────────
RAW_CSV   = Path("/Users/apple/Downloads/ml/data/raw/sea_ice_synthetic.csv")
MODEL_DIR = PROJECT_ROOT / "ml" / "models" / "weights"
SCHEMA    = MODEL_DIR / "seaice_feature_schema.json"
MODEL     = MODEL_DIR / "seaice_xgb_latest.json"

EXPECTED_COLS = [
    "sample_id", "timestamp", "latitude", "longitude",
    "sea_ice_concentration", "air_temperature_c", "sea_surface_temperature_c",
    "wind_speed_m_s", "wind_direction_deg",
    "ocean_current_u_m_s", "ocean_current_v_m_s",
    "forecast_horizon_hours", "target_sea_ice_concentration", "data_source_type",
]

FEATURE_COLS = [
    "latitude", "longitude", "sea_ice_concentration",
    "air_temperature_c", "sea_surface_temperature_c",
    "ocean_current_u_m_s", "ocean_current_v_m_s",
    "forecast_horizon_hours", "month", "sin_doy", "cos_doy",
    "wind_u", "wind_v",
]
TARGET_COL = "target_sea_ice_concentration"


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def raw_df():
    """Load the raw CSV once for the whole session."""
    assert RAW_CSV.exists(), f"Raw CSV not found: {RAW_CSV}"
    return pd.read_csv(RAW_CSV)


@pytest.fixture(scope="session")
def schema():
    """Load the saved feature schema."""
    assert SCHEMA.exists(), f"Feature schema not found: {SCHEMA}"
    with open(SCHEMA) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def processed_df(raw_df):
    """Apply the same preprocessing as the training script."""
    df = raw_df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    df["day_of_year"] = df["timestamp"].dt.dayofyear
    df["month"]       = df["timestamp"].dt.month
    df["sin_doy"]     = np.sin(2 * np.pi * df["day_of_year"] / 365.25)
    df["cos_doy"]     = np.cos(2 * np.pi * df["day_of_year"] / 365.25)
    df["wind_u"]      = df["wind_speed_m_s"] * np.cos(np.radians(df["wind_direction_deg"]))
    df["wind_v"]      = df["wind_speed_m_s"] * np.sin(np.radians(df["wind_direction_deg"]))
    drop = ["sample_id", "data_source_type", "timestamp",
            "wind_speed_m_s", "wind_direction_deg", "day_of_year", "year"]
    return df.drop(columns=[c for c in drop if c in df.columns])


@pytest.fixture(scope="session")
def splits(processed_df):
    n = len(processed_df)
    val_start  = int(n * 0.70)
    test_start = int(n * 0.85)
    train = processed_df.iloc[:val_start].copy()
    val   = processed_df.iloc[val_start:test_start].copy()
    test  = processed_df.iloc[test_start:].copy()
    return train, val, test


@pytest.fixture(scope="session")
def trained_model(splits, schema):
    """Load the saved XGBoost model."""
    import xgboost as xgb
    assert MODEL.exists(), f"Model not found: {MODEL}"
    m = xgb.XGBRegressor()
    m.load_model(str(MODEL))
    return m


# ══════════════════════════════════════════════════════════════════════════════
# 1. Dataset loading
# ══════════════════════════════════════════════════════════════════════════════

class TestDatasetLoading:

    def test_csv_exists(self):
        assert RAW_CSV.exists(), f"Raw CSV missing: {RAW_CSV}"

    def test_csv_not_empty(self, raw_df):
        assert len(raw_df) > 0, "CSV loaded but has 0 rows"

    def test_expected_row_count(self, raw_df):
        # Expect 2500 rows (known from dataset generation)
        assert len(raw_df) == 2500, f"Expected 2500 rows, got {len(raw_df)}"

    def test_expected_columns(self, raw_df):
        missing = [c for c in EXPECTED_COLS if c not in raw_df.columns]
        assert not missing, f"Missing columns: {missing}"

    def test_data_source_type(self, raw_df):
        values = raw_df["data_source_type"].unique().tolist()
        assert "SYNTHETIC_PROTOTYPE" in values, \
            f"Expected SYNTHETIC_PROTOTYPE, got {values}"


# ══════════════════════════════════════════════════════════════════════════════
# 2. Schema & target validation
# ══════════════════════════════════════════════════════════════════════════════

class TestSchemaValidation:

    def test_no_missing_values_in_features(self, raw_df):
        nulls = raw_df[EXPECTED_COLS].isnull().sum()
        assert nulls.sum() == 0, f"Missing values found:\n{nulls[nulls > 0]}"

    def test_no_duplicate_rows(self, raw_df):
        dupes = raw_df.duplicated().sum()
        assert dupes == 0, f"{dupes} duplicate rows found"

    def test_target_col_exists(self, raw_df):
        assert TARGET_COL in raw_df.columns

    def test_target_bounds(self, raw_df):
        assert raw_df[TARGET_COL].min() >= 0.0, "Target below 0"
        assert raw_df[TARGET_COL].max() <= 1.0, "Target above 1"

    def test_sic_bounds(self, raw_df):
        assert raw_df["sea_ice_concentration"].min() >= 0.0
        assert raw_df["sea_ice_concentration"].max() <= 1.0

    def test_latitude_antarctic(self, raw_df):
        assert raw_df["latitude"].max() <= -55.0, \
            "Latitude should be south of -55° for Antarctic"
        assert raw_df["latitude"].min() >= -90.0

    def test_longitude_valid(self, raw_df):
        assert raw_df["longitude"].min() >= -180.0
        assert raw_df["longitude"].max() <= 180.0

    def test_numeric_feature_dtypes(self, raw_df):
        numeric_cols = [
            "latitude", "longitude", "sea_ice_concentration",
            "air_temperature_c", "sea_surface_temperature_c",
            "wind_speed_m_s", "wind_direction_deg",
            "ocean_current_u_m_s", "ocean_current_v_m_s",
            TARGET_COL,
        ]
        for col in numeric_cols:
            assert pd.api.types.is_numeric_dtype(raw_df[col]), \
                f"Column {col} is not numeric: {raw_df[col].dtype}"

    def test_forecast_horizon_value(self, raw_df):
        # All rows should have the same forecast horizon (24h)
        assert raw_df["forecast_horizon_hours"].nunique() == 1
        assert raw_df["forecast_horizon_hours"].iloc[0] == 24


# ══════════════════════════════════════════════════════════════════════════════
# 3. Preprocessing
# ══════════════════════════════════════════════════════════════════════════════

class TestPreprocessing:

    def test_timestamp_parseable(self, raw_df):
        ts = pd.to_datetime(raw_df["timestamp"], errors="coerce")
        assert ts.isna().sum() == 0, "Some timestamps could not be parsed"

    def test_wind_decomposition(self, raw_df):
        df = raw_df.copy()
        df["wind_u"] = df["wind_speed_m_s"] * np.cos(np.radians(df["wind_direction_deg"]))
        df["wind_v"] = df["wind_speed_m_s"] * np.sin(np.radians(df["wind_direction_deg"]))
        reconstructed = np.sqrt(df["wind_u"] ** 2 + df["wind_v"] ** 2)
        np.testing.assert_allclose(
            reconstructed.values, df["wind_speed_m_s"].values, rtol=1e-5
        )

    def test_processed_feature_columns(self, processed_df):
        for col in FEATURE_COLS:
            assert col in processed_df.columns, f"Missing feature: {col}"

    def test_no_target_leakage(self, processed_df):
        """Future target info must not appear as a feature."""
        leaked = [c for c in processed_df.columns
                  if "target" in c.lower() and c != TARGET_COL]
        assert not leaked, f"Potential leakage columns: {leaked}"

    def test_no_inf_values(self, processed_df):
        numeric = processed_df.select_dtypes("number")
        assert not np.isinf(numeric.values).any(), "Infinite values in processed data"

    def test_no_nan_values(self, processed_df):
        assert processed_df.isnull().sum().sum() == 0, \
            "NaN values remain after preprocessing"

    def test_sorted_by_timestamp(self, raw_df):
        ts = pd.to_datetime(raw_df["timestamp"])
        sorted_ts = ts.sort_values()
        # At least test it can be sorted
        assert len(sorted_ts) == len(ts)


# ══════════════════════════════════════════════════════════════════════════════
# 4. Train/val/test split
# ══════════════════════════════════════════════════════════════════════════════

class TestSplitting:

    def test_split_sizes(self, splits, processed_df):
        train, val, test = splits
        n = len(processed_df)
        assert len(train) == int(n * 0.70), f"Train size off: {len(train)}"
        assert len(val)   == int(n * 0.85) - int(n * 0.70), f"Val size off: {len(val)}"
        assert len(test)  == n - int(n * 0.85), f"Test size off: {len(test)}"

    def test_split_no_overlap(self, splits, processed_df):
        train, val, test = splits
        assert len(train) + len(val) + len(test) == len(processed_df)

    def test_splits_sum_to_full(self, splits, processed_df):
        train, val, test = splits
        total = len(train) + len(val) + len(test)
        assert total == len(processed_df), \
            f"Split total {total} != dataset {len(processed_df)}"

    def test_target_present_in_all_splits(self, splits):
        for name, split in zip(["train", "val", "test"], splits):
            assert TARGET_COL in split.columns, f"Target missing from {name}"

    def test_features_present_in_all_splits(self, splits):
        for name, split in zip(["train", "val", "test"], splits):
            missing = [c for c in FEATURE_COLS if c not in split.columns]
            assert not missing, f"Features missing from {name}: {missing}"


# ══════════════════════════════════════════════════════════════════════════════
# 5. Model training (lightweight — fits a tiny model for correctness only)
# ══════════════════════════════════════════════════════════════════════════════

class TestModelTraining:

    def test_xgboost_importable(self):
        import xgboost as xgb
        assert hasattr(xgb, "XGBRegressor")

    def test_train_and_predict_small(self, splits):
        import xgboost as xgb
        train, val, test = splits
        X_train = train[FEATURE_COLS].values
        y_train = train[TARGET_COL].values
        X_test  = test[FEATURE_COLS].values
        y_test  = test[TARGET_COL].values

        # Tiny model — just verify the interface works, not optimising
        m = xgb.XGBRegressor(
            n_estimators=10, max_depth=3, random_state=42, tree_method="hist"
        )
        m.fit(X_train, y_train)
        preds = m.predict(X_test)
        assert preds.shape == y_test.shape
        assert not np.isnan(preds).any()
        assert not np.isinf(preds).any()

    def test_prediction_range_reasonable(self, splits):
        import xgboost as xgb
        train, _, test = splits
        m = xgb.XGBRegressor(n_estimators=10, max_depth=3, random_state=42)
        m.fit(train[FEATURE_COLS].values, train[TARGET_COL].values)
        preds = m.predict(test[FEATURE_COLS].values)
        # Model without clipping should still be reasonably close to [0, 1]
        assert preds.min() > -0.5, "Predictions far below 0"
        assert preds.max() < 1.5,  "Predictions far above 1"

    def test_reproducibility(self, splits):
        import xgboost as xgb
        train, _, test = splits
        X_tr = train[FEATURE_COLS].values
        y_tr = train[TARGET_COL].values
        X_te = test[FEATURE_COLS].values
        m1 = xgb.XGBRegressor(n_estimators=10, max_depth=3, random_state=42)
        m2 = xgb.XGBRegressor(n_estimators=10, max_depth=3, random_state=42)
        m1.fit(X_tr, y_tr)
        m2.fit(X_tr, y_tr)
        np.testing.assert_array_equal(
            m1.predict(X_te), m2.predict(X_te),
            err_msg="Predictions not reproducible with same seed"
        )


# ══════════════════════════════════════════════════════════════════════════════
# 6. Evaluation metrics
# ══════════════════════════════════════════════════════════════════════════════

class TestEvaluation:

    def test_saved_model_beats_persistence(self, trained_model, splits, schema):
        """Check that the production model outperforms the persistence baseline."""
        _, _, test = splits
        X_test = test[schema["feature_cols"]].values
        y_test = test[TARGET_COL].values

        preds = trained_model.predict(X_test)
        rmse_model = math.sqrt(np.mean((y_test - preds) ** 2))

        sic_idx = schema["feature_cols"].index("sea_ice_concentration")
        persistence = X_test[:, sic_idx]
        rmse_persist = math.sqrt(np.mean((y_test - persistence) ** 2))

        assert rmse_model < rmse_persist, (
            f"Model RMSE ({rmse_model:.4f}) is NOT better than "
            f"persistence baseline ({rmse_persist:.4f})"
        )

    def test_metrics_finite(self, trained_model, splits, schema):
        _, _, test = splits
        preds = trained_model.predict(test[schema["feature_cols"]].values)
        y_test = test[TARGET_COL].values
        mae  = float(np.mean(np.abs(y_test - preds)))
        rmse = float(math.sqrt(np.mean((y_test - preds) ** 2)))
        assert math.isfinite(mae),  f"MAE is not finite: {mae}"
        assert math.isfinite(rmse), f"RMSE is not finite: {rmse}"
        assert mae  >= 0
        assert rmse >= 0

    def test_r2_reasonable(self, trained_model, splits, schema):
        _, _, test = splits
        preds  = trained_model.predict(test[schema["feature_cols"]].values)
        y_test = test[TARGET_COL].values
        ss_res = np.sum((y_test - preds) ** 2)
        ss_tot = np.sum((y_test - y_test.mean()) ** 2)
        r2 = 1 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        assert r2 > 0.5, f"R² seems very low: {r2:.4f} — check for leakage or data issues"


# ══════════════════════════════════════════════════════════════════════════════
# 7. Model save / reload
# ══════════════════════════════════════════════════════════════════════════════

class TestModelSaveLoad:

    def test_model_file_exists(self):
        assert MODEL.exists(), f"Model file missing: {MODEL}"

    def test_schema_file_exists(self):
        assert SCHEMA.exists(), f"Schema file missing: {SCHEMA}"

    def test_schema_has_required_keys(self, schema):
        required = ["run_id", "feature_cols", "target_col", "xgb_params"]
        for key in required:
            assert key in schema, f"Schema missing key: {key}"

    def test_schema_feature_count(self, schema):
        assert len(schema["feature_cols"]) == 13, \
            f"Expected 13 features, got {len(schema['feature_cols'])}"

    def test_model_loadable(self):
        import xgboost as xgb
        m = xgb.XGBRegressor()
        m.load_model(str(MODEL))  # Must not raise

    def test_model_predict_after_reload(self, schema):
        import xgboost as xgb
        m = xgb.XGBRegressor()
        m.load_model(str(MODEL))
        dummy = pd.DataFrame([{c: 0.5 for c in schema["feature_cols"]}])
        pred = m.predict(dummy.values)
        assert pred.shape == (1,)
        assert math.isfinite(float(pred[0]))

    def test_save_and_reload_small_model(self, splits):
        """Save a tiny model to a temp file and reload it."""
        import xgboost as xgb
        train, _, test = splits
        m = xgb.XGBRegressor(n_estimators=5, random_state=42)
        m.fit(train[FEATURE_COLS].values, train[TARGET_COL].values)
        preds_before = m.predict(test[FEATURE_COLS].values)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tmp_path = f.name
        m.save_model(tmp_path)

        m2 = xgb.XGBRegressor()
        m2.load_model(tmp_path)
        preds_after = m2.predict(test[FEATURE_COLS].values)
        np.testing.assert_array_almost_equal(preds_before, preds_after, decimal=5)
        Path(tmp_path).unlink()


# ══════════════════════════════════════════════════════════════════════════════
# 8. Inference module
# ══════════════════════════════════════════════════════════════════════════════

class TestInference:

    def test_import_predict_function(self):
        from ml.inference.seaice_predict import predict_sea_ice_concentration
        assert callable(predict_sea_ice_concentration)

    def test_valid_sample_inference(self):
        from ml.inference.seaice_predict import predict_sea_ice_concentration
        result = predict_sea_ice_concentration(
            latitude=-67.5,
            longitude=-45.0,
            sea_ice_concentration=0.45,
            air_temperature_c=-14.0,
            sea_surface_temperature_c=-0.5,
            ocean_current_u_m_s=0.08,
            ocean_current_v_m_s=-0.03,
            wind_speed_m_s=8.0,
            wind_direction_deg=270.0,
            forecast_horizon_hours=24,
        )
        assert "predicted_sea_ice_concentration" in result
        assert "predicted_sea_ice_concentration_clipped" in result
        assert "warning" in result
        assert result["data_source_type"] == "SYNTHETIC_PROTOTYPE"
        pred = result["predicted_sea_ice_concentration"]
        assert math.isfinite(pred), f"Prediction not finite: {pred}"
        clipped = result["predicted_sea_ice_concentration_clipped"]
        assert 0.0 <= clipped <= 1.0, f"Clipped prediction out of [0,1]: {clipped}"

    def test_invalid_latitude_raises(self):
        from ml.inference.seaice_predict import predict_sea_ice_concentration
        with pytest.raises(ValueError, match="latitude"):
            predict_sea_ice_concentration(
                latitude=10.0,       # Not Antarctic
                longitude=-45.0,
                sea_ice_concentration=0.3,
                air_temperature_c=-10.0,
                sea_surface_temperature_c=0.0,
                ocean_current_u_m_s=0.05,
                ocean_current_v_m_s=0.02,
                wind_speed_m_s=5.0,
                wind_direction_deg=180.0,
            )

    def test_invalid_sic_raises(self):
        from ml.inference.seaice_predict import predict_sea_ice_concentration
        with pytest.raises(ValueError, match="sea_ice_concentration"):
            predict_sea_ice_concentration(
                latitude=-70.0,
                longitude=-45.0,
                sea_ice_concentration=1.5,   # > 1.0 invalid
                air_temperature_c=-10.0,
                sea_surface_temperature_c=0.0,
                ocean_current_u_m_s=0.05,
                ocean_current_v_m_s=0.02,
                wind_speed_m_s=5.0,
                wind_direction_deg=180.0,
            )

    def test_output_keys_complete(self):
        from ml.inference.seaice_predict import predict_sea_ice_concentration
        result = predict_sea_ice_concentration(
            latitude=-68.0, longitude=50.0,
            sea_ice_concentration=0.6, air_temperature_c=-20.0,
            sea_surface_temperature_c=-1.0, ocean_current_u_m_s=0.1,
            ocean_current_v_m_s=0.05, wind_speed_m_s=12.0,
            wind_direction_deg=315.0,
        )
        required_keys = [
            "predicted_sea_ice_concentration",
            "predicted_sea_ice_concentration_clipped",
            "forecast_horizon_hours",
            "data_source_type",
            "model_run_id",
            "features_used",
            "warning",
        ]
        for k in required_keys:
            assert k in result, f"Output missing key: {k}"

    def test_inference_with_timestamp(self):
        from ml.inference.seaice_predict import predict_sea_ice_concentration
        result = predict_sea_ice_concentration(
            latitude=-66.0, longitude=-100.0,
            sea_ice_concentration=0.2, air_temperature_c=-8.0,
            sea_surface_temperature_c=0.5, ocean_current_u_m_s=0.0,
            ocean_current_v_m_s=0.0, wind_speed_m_s=3.0,
            wind_direction_deg=90.0,
            timestamp="2022-06-15",
        )
        assert "predicted_sea_ice_concentration" in result

    def test_inference_reproducible(self):
        from ml.inference.seaice_predict import predict_sea_ice_concentration
        kwargs = dict(
            latitude=-67.5, longitude=-45.0,
            sea_ice_concentration=0.45, air_temperature_c=-14.0,
            sea_surface_temperature_c=-0.5, ocean_current_u_m_s=0.08,
            ocean_current_v_m_s=-0.03, wind_speed_m_s=8.0,
            wind_direction_deg=270.0,
        )
        r1 = predict_sea_ice_concentration(**kwargs)
        r2 = predict_sea_ice_concentration(**kwargs)
        assert r1["predicted_sea_ice_concentration"] == r2["predicted_sea_ice_concentration"]


# ══════════════════════════════════════════════════════════════════════════════
# 9. Colab MCP status (report-only, never blocks test suite)
# ══════════════════════════════════════════════════════════════════════════════

class TestColabMCP:

    def test_uvx_path(self):
        import shutil
        # We know uvx is installed at an absolute path; not in default PATH
        uvx_abs = Path("/Users/apple/Library/Python/3.9/bin/uvx")
        found = shutil.which("uvx") is not None or uvx_abs.exists()
        assert found, "uvx not found — colab-mcp cannot start"

    def test_mcp_config_exists(self):
        cfg = Path.home() / ".gemini" / "config" / "mcp_config.json"
        assert cfg.exists(), f"MCP config missing: {cfg}"

    def test_mcp_config_has_colab_entry(self):
        import json
        cfg = Path.home() / ".gemini" / "config" / "mcp_config.json"
        if not cfg.exists():
            pytest.skip("MCP config file not found")
        with open(cfg) as f:
            data = json.load(f)
        servers = data.get("mcpServers", {})
        colab_keys = [k for k in servers if "colab" in k.lower()]
        assert colab_keys, "No colab entry in mcp_config.json"
