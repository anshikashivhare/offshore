import pandas as pd
from ml.benchmarks.evaluate import evaluate_trajectory_model, evaluate_seaice_model
from ml.benchmarks.baselines import TrajectoryPersistenceBaseline, SeaIcePersistenceBaseline
from ml.benchmarks.benchmark_report import generate_report
from ml.preprocessing.trajectory.data import generate_synthetic_tracks
from ml.preprocessing.seaice.data import generate_synthetic_timeseries
from ml.benchmarks.splits import time_based_split_per_entity_strict, time_based_split_strict

def main():
    print("Generating trajectory data...")
    traj_df = generate_synthetic_tracks(time_varying_env=True)
    _, _, traj_test = time_based_split_per_entity_strict(traj_df, entity_col="iceberg_id")
    
    print("Generating sea-ice data...")
    seaice_df = generate_synthetic_timeseries(spatial_correlation=True)
    # create a naive lag_1 feature for persistence
    seaice_df["lag_1"] = seaice_df.groupby(["row", "col"])["concentration"].shift(1)
    seaice_df = seaice_df.dropna()
    _, _, seaice_test = time_based_split_strict(seaice_df, sort_col="date")
    
    # Baselines
    traj_baseline = TrajectoryPersistenceBaseline()
    seaice_baseline = SeaIcePersistenceBaseline()
    
    print("Evaluating models...")
    traj_res = evaluate_trajectory_model(
        traj_baseline, 
        traj_test, 
        feature_cols=[], 
        target_cols=["next_delta_lat", "next_delta_lon"],
        is_baseline=True
    )
    
    seaice_res = evaluate_seaice_model(
        seaice_baseline,
        seaice_test,
        feature_cols=[],
        target_col="concentration",
        is_baseline=True
    )
    
    results = {
        "trajectory": {"persistence": traj_res},
        "sea_ice": {"persistence": seaice_res}
    }
    
    print("Generating report...")
    generate_report(results, report_dir="ml/benchmarks/reports")
    print("Done!")

if __name__ == "__main__":
    main()
