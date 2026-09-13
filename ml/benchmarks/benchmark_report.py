import json
from datetime import datetime
from pathlib import Path


def generate_report(results, report_dir="."):
    report_dir = Path(report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().isoformat()

    # Machine readable JSON
    json_path = report_dir / "benchmark_results.json"
    with open(json_path, "w") as f:
        json.dump({"timestamp": timestamp, "results": results}, f, indent=2)

    # Human readable text
    txt_path = report_dir / "benchmark_report.txt"
    with open(txt_path, "w") as f:
        f.write("MODEL BENCHMARK REPORT\n")
        f.write("======================\n\n")
        f.write(f"Timestamp: {timestamp}\n\n")

        for task, task_results in results.items():
            f.write(f"--------------------------------\n")
            f.write(f"{task.upper()} PREDICTION\n")
            f.write(f"--------------------------------\n\n")

            for model_name, model_results in task_results.items():
                f.write(f"Model: {model_name}\n")

                # Overall
                if "overall" in model_results:
                    f.write("  Overall Metrics:\n")
                    for k, v in model_results["overall"].items():
                        f.write(f"    {k}: {v:.5f}\n")

                # Hard cases
                hard_cases = {k: v for k, v in model_results.items() if k != "overall"}
                if hard_cases:
                    f.write("  Hard Cases:\n")
                    for hc_name, hc_metrics in hard_cases.items():
                        f.write(f"    {hc_name}:\n")
                        for k, v in hc_metrics.items():
                            f.write(f"      {k}: {v:.5f}\n")
                f.write("\n")

    return str(json_path), str(txt_path)
