"""
Structured, persistent logging of every training run: what model, what
data source, what metrics came out, when, and (if available) what git
commit produced it. Appends to a JSON Lines file so it's diffable,
greppable, and needs no database at this project's scale.
"""

import json
import subprocess
import datetime
from pathlib import Path


def _get_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=2,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def log_experiment(
    model_name: str,
    data_source: str,
    metrics: dict,
    hyperparams: dict = None,
    log_path: str = "mlops/experiment_log.jsonl",
) -> dict:
    record = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "model_name": model_name,
        "data_source": data_source,
        "metrics": metrics,
        "hyperparams": hyperparams or {},
        "git_commit": _get_git_commit(),
    }

    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")

    return record


def get_experiment_history(model_name: str = None, log_path: str = "mlops/experiment_log.jsonl") -> list:
    path = Path(log_path)
    if not path.exists():
        return []

    records = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if model_name is None or record["model_name"] == model_name:
                records.append(record)
    return records


def get_latest_metric(model_name: str, metric_name: str, log_path: str = "mlops/experiment_log.jsonl"):
    """Used by the retraining trigger to compare current performance
    against the last known-good run."""
    history = get_experiment_history(model_name, log_path)
    if not history:
        return None
    return history[-1]["metrics"].get(metric_name)
