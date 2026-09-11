"""
Decides whether a model should be retrained: data drift OR performance
degradation vs production. Either alone triggers a retrain recommendation.
"""

import logging
from mlops.model_registry import get_production_info
from mlops.experiment_log import get_latest_metric

logger = logging.getLogger("mlops.retrain_trigger")


def should_retrain(
    model_name: str,
    metric_name: str,
    drift_warnings: list = None,
    degradation_threshold_pct: float = 15.0,
) -> dict:
    reasons = []

    if drift_warnings:
        reasons.append(f"data drift detected ({len(drift_warnings)} check(s) triggered)")

    production = get_production_info(model_name)
    latest_metric = get_latest_metric(model_name, metric_name)

    if production is None:
        reasons.append("no production model exists yet — initial training needed")
    elif latest_metric is not None:
        prod_value = production["metric_value"]
        if prod_value > 0:
            pct_worse = ((latest_metric - prod_value) / prod_value) * 100
            if pct_worse > degradation_threshold_pct:
                reasons.append(
                    f"latest {metric_name} ({latest_metric:.5f}) is {pct_worse:.1f}% worse than "
                    f"production ({prod_value:.5f}), exceeding {degradation_threshold_pct}% threshold"
                )

    decision = {"retrain": len(reasons) > 0, "reasons": reasons}
    if decision["retrain"]:
        logger.info(f"Retrain recommended for {model_name}: {'; '.join(reasons)}")
    else:
        logger.info(f"No retrain needed for {model_name} — production model still performing within tolerance")
    return decision
