# ML Benchmark & Evaluation Framework

## Purpose
The purpose of this framework is to establish objective metrics for what the ML models are predicting, how they compare against simple baselines, and where they fail. This benchmark is specifically NOT meant to determine physical vessel safety; it only measures ML prediction accuracy (e.g. geographic position error, mean absolute error). Downstream route and risk engines handle safety rules based on these predictions.

## Methodology

### Data Splitting
To prevent data leakage (especially overlapping windows in sequence models), the data is strictly split chronologically into Train (70%), Validation (15%), and Test (15%) partitions **before** any sequence generation or scaling occurs.

### Baselines
To prove that our models are actually learning useful temporal/environmental patterns, they must beat a simple `Persistence` baseline:
- **Trajectory Persistence**: Predicts the iceberg does not move relative to its current trajectory (predicts `delta = 0`).
- **Sea-Ice Persistence**: Predicts tomorrow's concentration will exactly match today's.

### Metrics
- **Trajectory**: Mean Absolute Error (MAE), Root Mean Square Error (RMSE), and Geographic Position Error (calculated in actual kilometers via Haversine).
- **Sea-Ice**: MAE and RMSE of concentration predictions.

### Hard Cases
Models are evaluated overall and across "hard cases" derived from actual environmental features (e.g., strong winds, high ocean currents, high ice concentration).

## How to use
```python
from ml.benchmarks.evaluate import evaluate_trajectory_model
from ml.benchmarks.benchmark_report import generate_report

results = evaluate_trajectory_model(model, df_test, feature_cols, target_cols)
generate_report({"trajectory": {"my_model": results}}, "reports_dir")
```

## TBD
Acceptance/Domain thresholds (e.g., maximum acceptable km error for navigation) are currently marked as `null`/`TBD` awaiting authoritative safety requirements.
