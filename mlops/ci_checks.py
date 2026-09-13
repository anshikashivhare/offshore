"""
CI sanity checks — catches catastrophic regressions (silently broken
metrics), not strict performance targets. Bounds are deliberately
loose; tight thresholds belong in retrain_trigger.py, not here.

Run: python -m mlops.ci_checks
"""

import sys

from mlops.experiment_log import get_latest_metric

SANITY_BOUNDS = [
    ("seaice_xgboost", "test_rmse", 0.0, 0.3),
    ("seaice_convlstm", "test_rmse", 0.0, 0.3),
    ("trajectory_xgboost", "rmse_lat", 0.0, 0.1),
    ("trajectory_xgboost", "rmse_lon", 0.0, 0.1),
    ("trajectory_lstm", "rmse_lat", 0.0, 0.1),
    ("trajectory_lstm", "rmse_lon", 0.0, 0.1),
]


def run_checks() -> bool:
    all_passed = True
    print("=" * 60)
    print("CI SANITY CHECKS")
    print("=" * 60)

    for model_name, metric_name, min_allowed, max_allowed in SANITY_BOUNDS:
        value = get_latest_metric(model_name, metric_name)
        if value is None:
            print(f"SKIP  {model_name}.{metric_name} — no logged run found")
            continue
        if value != value:  # NaN check
            print(f"FAIL  {model_name}.{metric_name} = NaN")
            all_passed = False
        elif not (min_allowed <= value <= max_allowed):
            print(
                f"FAIL  {model_name}.{metric_name} = {value:.5f} — outside [{min_allowed}, {max_allowed}]"
            )
            all_passed = False
        else:
            print(f"PASS  {model_name}.{metric_name} = {value:.5f}")

    print("=" * 60)
    print("ALL CHECKS PASSED" if all_passed else "SOME CHECKS FAILED")
    print("=" * 60)
    return all_passed


if __name__ == "__main__":
    sys.exit(0 if run_checks() else 1)
