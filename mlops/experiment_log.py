"""
Structured, persistent logging of every training run: what model, what
data source, what metrics came out, when, and (if available) what git
commit produced it. Appends to a JSON Lines file so it's diffable,
greppable, and needs no database at this project's scale.
"""

import datetime
import fcntl
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict

from ml.path_utils import get_mlops_path

DEFAULT_LOG_PATH = get_mlops_path("experiment_log.jsonl")


@dataclass
class ExperimentRecord:
    run_id: str
    timestamp: str
    model_name: str
    data_source: str
    artifact_uri: str
    metrics: Dict[str, float]
    hyperparams: Dict[str, Any]
    git_commit: str

    def __post_init__(self):
        # Strict schema validation
        if not isinstance(self.metrics, dict):
            raise ValueError("metrics must be a dictionary")
        if not isinstance(self.hyperparams, dict):
            raise ValueError("hyperparams must be a dictionary")


def _get_git_commit() -> str:
    commit = "unknown"
    try:
        # Get hash
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            commit = result.stdout.strip()

            # Check for uncommitted changes
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if status_result.returncode == 0 and status_result.stdout.strip():
                commit += "-dirty"
    except Exception:
        pass
    return commit


def log_experiment(
    run_id: str,
    model_name: str,
    data_source: str,
    artifact_uri: str,
    metrics: dict,
    hyperparams: dict = None,
    log_path: str = DEFAULT_LOG_PATH,
) -> dict:
    record_obj = ExperimentRecord(
        run_id=run_id,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        model_name=model_name,
        data_source=data_source,
        artifact_uri=artifact_uri,
        metrics=metrics,
        hyperparams=hyperparams or {},
        git_commit=_get_git_commit(),
    )

    record_dict = asdict(record_obj)

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Atomic file append using fcntl
    with open(path, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.write(json.dumps(record_dict) + "\n")
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

    return record_dict


def get_experiment_history(
    model_name: str = None, log_path: str = DEFAULT_LOG_PATH
) -> list:
    path = Path(log_path)
    if not path.exists():
        return []

    records = []
    with open(path) as f:
        # No lock needed for simple reading
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if model_name is None or record.get("model_name") == model_name:
                records.append(record)
    return records


def get_latest_metric(
    model_name: str, metric_name: str, log_path: str = DEFAULT_LOG_PATH
):
    """Used by the retraining trigger to compare current performance
    against the last known-good run."""
    history = get_experiment_history(model_name, log_path)
    if not history:
        return None
    # Assuming history is ordered chronologically by append order
    return history[-1].get("metrics", {}).get(metric_name)


def get_best_metric(
    model_name: str,
    metric_name: str,
    optimize: str = "min",
    log_path: str = DEFAULT_LOG_PATH,
):
    """Fetch the optimal historical performance for a given metric across all runs."""
    history = get_experiment_history(model_name, log_path)
    values = [
        r.get("metrics", {}).get(metric_name)
        for r in history
        if r.get("metrics", {}).get(metric_name) is not None
    ]

    if not values:
        return None

    if optimize == "min":
        return min(values)
    elif optimize == "max":
        return max(values)
    else:
        raise ValueError("optimize must be 'min' or 'max'")
