"""
The continuous-training entry point: checks whether retraining is
warranted (drift or degradation), retrains if so, and only promotes
the result to production if it beats the current production model.

Run: python -m mlops.continuous_training --model seaice_xgboost
"""

import argparse
import logging

from ml.path_utils import get_model_path
from mlops.drift_detection import detect_drift, load_reference_statistics
from mlops.experiment_log import get_experiment_history, get_latest_metric
from mlops.model_registry import promote_if_better
from mlops.retrain_trigger import should_retrain

logger = logging.getLogger("mlops.continuous_training")

MODEL_CONFIGS = {
    "seaice_xgboost": {
        "metric_name": "test_rmse",
        "production_model_path": get_model_path("production_seaice_xgb.json"),
        "drift_reference_path": get_model_path("reference_stats.json"),
        "drift_columns": ["concentration"],
    },
    "trajectory_xgboost": {
        "metric_name": "rmse_lat",
        "production_model_path": get_model_path("production_trajectory_model.joblib"),
        "drift_reference_path": get_model_path("reference_stats.json"),
        "drift_columns": ["current_u", "current_v", "wind_u", "wind_v"],
    },
    "seaice_convlstm": {
        "metric_name": "test_rmse",
        "production_model_path": get_model_path("production_convlstm.pt"),
        "drift_reference_path": get_model_path(
            "reference_stats.json"
        ),  # shared with seaice_xgboost
        "drift_columns": ["concentration"],
    },
    "trajectory_lstm": {
        "metric_name": "rmse_lat",
        "production_model_path": get_model_path("production_lstm_model.pt"),
        "drift_reference_path": get_model_path("reference_stats.json"),
        "drift_columns": ["current_u", "current_v", "wind_u", "wind_v"],
    },
}


def check_and_retrain(
    model_name: str, new_data_df=None, train_fn=None, force: bool = False
) -> dict:
    config = MODEL_CONFIGS[model_name]

    drift_warnings = []
    if new_data_df is not None:
        try:
            ref_stats = load_reference_statistics(config["drift_reference_path"])
            drift_warnings = detect_drift(
                new_data_df, ref_stats, config["drift_columns"]
            )
        except FileNotFoundError:
            logger.info(
                f"No reference statistics yet for {model_name} — skipping drift check this run"
            )

    decision = should_retrain(
        model_name, config["metric_name"], drift_warnings=drift_warnings
    )

    if not force and not decision["retrain"]:
        return {
            "action": "skipped",
            "reasons": decision["reasons"] or ["no trigger conditions met"],
        }

    if train_fn is None:
        return {
            "action": "retrain_needed_but_no_train_fn_provided",
            "reasons": decision["reasons"],
        }

    logger.info(
        f"Retraining {model_name}. Reasons: {decision['reasons'] or ['forced']}"
    )
    train_fn()

    history = get_experiment_history(model_name)
    if not history:
        return {
            "action": "retrain_failed",
            "reason": "training ran but no record was logged",
        }

    latest_run = history[-1]
    new_metric = latest_run.get("metrics", {}).get(config["metric_name"])
    if new_metric is None:
        return {
            "action": "retrain_failed",
            "reason": "training ran but no metric was logged",
        }

    candidate_model_path = latest_run.get("artifact_uri")
    if not candidate_model_path:
        return {
            "action": "retrain_failed",
            "reason": "training ran but no artifact_uri was logged",
        }

    promotion = promote_if_better(
        model_name=model_name,
        candidate_metric_value=new_metric,
        metric_name=config["metric_name"],
        candidate_model_path=candidate_model_path,
        production_model_path=config["production_model_path"],
    )

    return {
        "action": "retrained",
        "trigger_reasons": decision["reasons"],
        "new_metric": new_metric,
        "promotion": promotion,
    }


from unittest import mock

# ==========================================
# Unit Tests (Run with: pytest mlops/continuous_training.py)
# ==========================================
import pytest


@pytest.fixture
def mock_should_retrain():
    with mock.patch(f"{__name__}.should_retrain") as m:
        yield m


@pytest.fixture
def mock_get_latest_metric():
    with mock.patch(f"{__name__}.get_latest_metric") as m:
        yield m


@pytest.fixture
def mock_promote_if_better():
    with mock.patch(f"{__name__}.promote_if_better") as m:
        yield m


def test_skip_when_no_conditions_met(mock_should_retrain):
    mock_should_retrain.return_value = {"retrain": False, "reasons": []}

    result = check_and_retrain("seaice_xgboost", force=False)

    assert result["action"] == "skipped"
    assert result["reasons"] == ["no trigger conditions met"]


def test_force_retraining(
    mock_should_retrain, mock_get_latest_metric, mock_promote_if_better
):
    # Even if should_retrain says no, --force overrides it
    mock_should_retrain.return_value = {"retrain": False, "reasons": []}
    mock_get_latest_metric.return_value = 1.2
    mock_promote_if_better.return_value = {
        "promoted": True,
        "reason": "Better than production",
    }

    mock_train_fn = mock.Mock()

    result = check_and_retrain("seaice_xgboost", train_fn=mock_train_fn, force=True)

    assert result["action"] == "retrained"
    mock_train_fn.assert_called_once()
    mock_get_latest_metric.assert_called_once_with(
        "seaice_xgboost", MODEL_CONFIGS["seaice_xgboost"]["metric_name"]
    )
    mock_promote_if_better.assert_called_once()


def test_retrain_and_promote(
    mock_should_retrain, mock_get_latest_metric, mock_promote_if_better
):
    mock_should_retrain.return_value = {"retrain": True, "reasons": ["drift detected"]}
    mock_get_latest_metric.return_value = 0.5
    mock_promote_if_better.return_value = {
        "promoted": True,
        "reason": "Better than production",
    }

    mock_train_fn = mock.Mock()

    result = check_and_retrain("trajectory_lstm", train_fn=mock_train_fn, force=False)

    assert result["action"] == "retrained"
    assert result["trigger_reasons"] == ["drift detected"]
    assert result["promotion"]["promoted"] is True
    mock_train_fn.assert_called_once()
    mock_promote_if_better.assert_called_once_with(
        model_name="trajectory_lstm",
        candidate_metric_value=0.5,
        metric_name=MODEL_CONFIGS["trajectory_lstm"]["metric_name"],
        candidate_model_path=MODEL_CONFIGS["trajectory_lstm"]["candidate_model_path"],
        production_model_path=MODEL_CONFIGS["trajectory_lstm"]["production_model_path"],
    )


def test_retrain_but_skip_promotion(
    mock_should_retrain, mock_get_latest_metric, mock_promote_if_better
):
    mock_should_retrain.return_value = {
        "retrain": True,
        "reasons": ["degradation detected"],
    }
    mock_get_latest_metric.return_value = 2.5
    mock_promote_if_better.return_value = {
        "promoted": False,
        "reason": "Worse than production",
    }

    mock_train_fn = mock.Mock()

    result = check_and_retrain("seaice_convlstm", train_fn=mock_train_fn, force=False)

    assert result["action"] == "retrained"
    assert result["promotion"]["promoted"] is False


def test_retrain_needed_but_no_train_fn(mock_should_retrain):
    mock_should_retrain.return_value = {"retrain": True, "reasons": ["drift detected"]}

    result = check_and_retrain("seaice_xgboost", force=False)

    assert result["action"] == "retrain_needed_but_no_train_fn_provided"
    assert result["reasons"] == ["drift detected"]


def test_retrain_failed_no_metric(mock_should_retrain, mock_get_latest_metric):
    mock_should_retrain.return_value = {"retrain": True, "reasons": ["drift detected"]}
    mock_get_latest_metric.return_value = None

    mock_train_fn = mock.Mock()

    result = check_and_retrain(
        "trajectory_xgboost", train_fn=mock_train_fn, force=False
    )

    assert result["action"] == "retrain_failed"
    assert result["reason"] == "training ran but no metric was logged"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True, choices=list(MODEL_CONFIGS.keys()))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.model == "seaice_xgboost":
        from ml.training.seaice_train import train_model

        result = check_and_retrain(
            "seaice_xgboost", train_fn=lambda: train_model(), force=args.force
        )
    elif args.model == "trajectory_xgboost":
        from ml.training.trajectory_train import train_model

        result = check_and_retrain(
            "trajectory_xgboost", train_fn=lambda: train_model(), force=args.force
        )
    elif args.model == "seaice_convlstm":
        from ml.training.seaice_train_convlstm import train_convlstm

        result = check_and_retrain(
            "seaice_convlstm", train_fn=lambda: train_convlstm(), force=args.force
        )
    elif args.model == "trajectory_lstm":
        from ml.training.trajectory_train_lstm import train_lstm

        result = check_and_retrain(
            "trajectory_lstm", train_fn=lambda: train_lstm(), force=args.force
        )

    print(result)
