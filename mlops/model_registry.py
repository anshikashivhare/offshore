"""
Tracks the currently "production" model per model_name — its metric
value, the path to its saved weights/model file, and when it was
promoted. A newly trained model only replaces production if it
actually beats it (champion-challenger pattern).
"""

import json
import shutil
import datetime
from pathlib import Path

from ml.path_utils import get_mlops_path

REGISTRY_PATH = get_mlops_path("model_registry.json")


def _load_registry(registry_path: str = REGISTRY_PATH) -> dict:
    path = Path(registry_path)
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def _save_registry(registry: dict, registry_path: str = REGISTRY_PATH) -> None:
    path = Path(registry_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(registry, f, indent=2)


def get_production_info(model_name: str, registry_path: str = REGISTRY_PATH) -> dict:
    registry = _load_registry(registry_path)
    return registry.get(model_name)


def promote_if_better(
    model_name: str,
    candidate_metric_value: float,
    metric_name: str,
    candidate_model_path: str,
    production_model_path: str,
    lower_is_better: bool = True,
    registry_path: str = REGISTRY_PATH,
) -> dict:
    current = get_production_info(model_name, registry_path)

    should_promote = False
    if current is None:
        should_promote = True
        reason = "no production model exists yet — promoting first candidate"
    else:
        prod_value = current["metric_value"]
        better = candidate_metric_value < prod_value if lower_is_better else candidate_metric_value > prod_value
        if better:
            should_promote = True
            reason = f"candidate {metric_name} {candidate_metric_value:.5f} beats production {prod_value:.5f}"
        else:
            reason = f"candidate {metric_name} {candidate_metric_value:.5f} does not beat production {prod_value:.5f} — keeping current production model"

    if should_promote:
        Path(production_model_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(candidate_model_path, production_model_path)

        registry = _load_registry(registry_path)
        registry[model_name] = {
            "metric_name": metric_name,
            "metric_value": candidate_metric_value,
            "model_path": production_model_path,
            "promoted_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }
        _save_registry(registry, registry_path)

    return {"promoted": should_promote, "reason": reason}
