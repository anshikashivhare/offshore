"""
Reads the experiment log and produces a readable summary of model
performance over time — a console report plus optional trend charts.
This is the "at a glance, is anything degrading" view, and the same
read path the retraining trigger uses to decide whether to fire.

Run: python -m mlops.monitor
"""

from ml.path_utils import get_mlops_path
from mlops.experiment_log import get_experiment_history

DEFAULT_TRENDS_PATH = get_mlops_path("metric_trends.png")

PRIMARY_METRIC = {
    "seaice_xgboost": "test_rmse",
    "seaice_convlstm": "test_rmse",
    "trajectory_xgboost": "rmse_lat",
    "trajectory_lstm": "rmse_lat",
}


def summarize(model_name: str) -> dict:
    metric_name = PRIMARY_METRIC.get(model_name)
    history = get_experiment_history(model_name)

    if not history:
        return {"model_name": model_name, "status": "no runs logged yet"}

    values = [
        h["metrics"].get(metric_name) for h in history if metric_name in h["metrics"]
    ]
    values = [v for v in values if v is not None]

    if not values:
        return {
            "model_name": model_name,
            "status": f"no '{metric_name}' metric found in logged runs",
        }

    latest = values[-1]
    best = min(values)
    trend = "N/A (first run)"
    if len(values) >= 2:
        prev = values[-2]
        if latest < prev:
            trend = f"improving ({prev:.5f} -> {latest:.5f})"
        elif latest > prev:
            trend = f"degrading ({prev:.5f} -> {latest:.5f})"
        else:
            trend = "unchanged"

    return {
        "model_name": model_name,
        "metric_name": metric_name,
        "run_count": len(history),
        "latest": latest,
        "best_ever": best,
        "trend": trend,
        "is_at_best": latest == best,
    }


def print_report():
    print("=" * 70)
    print("MODEL PERFORMANCE MONITORING REPORT")
    print("=" * 70)
    for model_name in PRIMARY_METRIC:
        summary = summarize(model_name)
        print(f"\n{model_name}")
        print("-" * len(model_name))
        if "status" in summary:
            print(f"  {summary['status']}")
            continue
        print(f"  Runs logged:     {summary['run_count']}")
        print(f"  Metric:          {summary['metric_name']}")
        print(f"  Latest value:    {summary['latest']:.5f}")
        print(f"  Best ever:       {summary['best_ever']:.5f}")
        print(f"  Trend:           {summary['trend']}")
        print(f"  At best:         {'yes' if summary['is_at_best'] else 'no'}")


def plot_trends(output_path: str = DEFAULT_TRENDS_PATH):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    models_with_data = []
    for model_name, metric_name in PRIMARY_METRIC.items():
        history = get_experiment_history(model_name)
        values = [
            h["metrics"].get(metric_name)
            for h in history
            if metric_name in h["metrics"]
        ]
        if values:
            models_with_data.append((model_name, metric_name, values))

    if not models_with_data:
        print("No data to plot yet — run some training scripts first.")
        return

    fig, axes = plt.subplots(
        1, len(models_with_data), figsize=(5 * len(models_with_data), 4)
    )
    if len(models_with_data) == 1:
        axes = [axes]

    for ax, (model_name, metric_name, values) in zip(axes, models_with_data):
        ax.plot(range(1, len(values) + 1), values, marker="o")
        ax.set_title(model_name)
        ax.set_xlabel("Run #")
        ax.set_ylabel(metric_name)
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    print(f"Saved trend chart to {output_path}")


if __name__ == "__main__":
    print_report()
    plot_trends()
