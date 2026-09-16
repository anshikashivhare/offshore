import pandas as pd
import numpy as np
from ml.benchmarks.evaluate import evaluate_trajectory_model, evaluate_seaice_model
from ml.benchmarks.baselines import TrajectoryPersistenceBaseline, SeaIcePersistenceBaseline
from ml.benchmarks.benchmark_report import generate_report
from ml.preprocessing.trajectory.data import generate_synthetic_tracks
from ml.preprocessing.seaice.data import generate_synthetic_timeseries
import torch
from ml.benchmarks.splits import time_based_split_per_entity_strict, time_based_split_strict
from ml.training.trajectory_train import train_model as train_traj_xgb
from ml.training.trajectory_train_lstm import train_lstm as train_traj_lstm
from ml.training.seaice_train import train_model as train_seaice_xgb
from ml.training.seaice_train_convlstm import train_convlstm as train_seaice_convlstm
from ml.preprocessing.trajectory.sequence_data import make_sequences as make_traj_sequences
from ml.preprocessing.seaice.grid_sequence import dataframe_to_grid_sequence, make_sequences as make_seaice_sequences

class LSTMModelWrapper:
    def __init__(self, model, original_df, seq_len=5):
        self.model = model
        self.original_df = original_df
        self.seq_len = seq_len
        self.model.eval()

    def predict(self, df):
        X, _ = make_traj_sequences(self.original_df, seq_len=self.seq_len)
        with torch.no_grad():
            preds = self.model(torch.tensor(X))
        return preds.numpy()

class ConvLSTMModelWrapper:
    def __init__(self, model, seq_len=5):
        self.model = model
        self.seq_len = seq_len
        self.model.eval()

    def predict(self, df):
        grid_seq = dataframe_to_grid_sequence(df)
        X, _ = make_seaice_sequences(grid_seq, input_len=self.seq_len)
        X_t = torch.tensor(X).unsqueeze(2)
        with torch.no_grad():
            preds = self.model(X_t)
        # return shape (N, rows, cols) which maps to df rows if flattened properly?
        # Actually evaluate_seaice_model uses preds[mask].
        # evaluate_seaice_model gets a flat df, but model predicts grids!
        pass # Wait, evaluate_seaice_model requires flat preds!

def get_aligned_traj_df(df, seq_len=5):
    frames = []
    for _, group in df.groupby("iceberg_id"):
        group = group.sort_values("timestep").reset_index(drop=True)
        # make_sequences yields elements aligned with t + seq_len - 1
        frames.append(group.iloc[seq_len - 1 : -1])
    return pd.concat(frames).reset_index(drop=True)

def get_aligned_seaice_df(df, seq_len=5):
    # For seaice, make_sequences yields elements aligned with t + seq_len
    # Wait, the time index for y in seaice is t + input_len
    dates = sorted(df["date"].unique())
    valid_dates = dates[seq_len:]
    return df[df["date"].isin(valid_dates)].sort_values(["date", "row", "col"]).reset_index(drop=True)

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
    
    # Train models
    traj_xgb_model, traj_lstm_model = None, None
    seaice_xgb_model, seaice_convlstm_model = None, None
    
    try:
        print("Training Trajectory XGBoost...")
        traj_xgb_model, _ = train_traj_xgb()
    except Exception as e:
        print(f"Error training Trajectory XGBoost: {e}")
    
    try:
        print("Training Trajectory LSTM...")
        traj_lstm_model, _, _ = train_traj_lstm()
    except Exception as e:
        print(f"Error training Trajectory LSTM: {e}")
    
    try:
        print("Training Sea-Ice XGBoost...")
        seaice_xgb_model, _, _ = train_seaice_xgb()
    except Exception as e:
        print(f"Error training Sea-Ice XGBoost: {e}")
    
    try:
        print("Training Sea-Ice ConvLSTM...")
        seaice_convlstm_model, _, _, _ = train_seaice_convlstm()
    except Exception as e:
        print(f"Error training Sea-Ice ConvLSTM: {e}")
    
    # Baselines
    traj_baseline = TrajectoryPersistenceBaseline()
    seaice_baseline = SeaIcePersistenceBaseline()
    
    print("Evaluating models...")
    # 1. Trajectory Persistence
    traj_res_persistence = evaluate_trajectory_model(
        traj_baseline, 
        traj_test, 
        feature_cols=[], 
        target_cols=["next_delta_lat", "next_delta_lon"],
        is_baseline=True
    )
    
    # 2. Trajectory XGBoost
    traj_res_xgb = None
    if traj_xgb_model is not None:
        try:
            traj_res_xgb = evaluate_trajectory_model(
                traj_xgb_model,
                traj_test,
                feature_cols=["lat", "lon", "current_u", "current_v", "wind_u", "wind_v"],
                target_cols=["next_delta_lat", "next_delta_lon"],
                is_baseline=False
            )
        except Exception as e:
            print(f"Error evaluating Trajectory XGBoost: {e}")
    
    # 3. Trajectory LSTM
    traj_res_lstm = None
    if traj_lstm_model is not None:
        try:
            aligned_traj_test = get_aligned_traj_df(traj_test, seq_len=5)
            traj_res_lstm = evaluate_trajectory_model(
                LSTMModelWrapper(traj_lstm_model, traj_test, seq_len=5),
                aligned_traj_test,
                feature_cols=[],
                target_cols=["next_delta_lat", "next_delta_lon"],
                is_baseline=False
            )
        except Exception as e:
            print(f"Error evaluating Trajectory LSTM: {e}")
    
    # 4. Sea-Ice Persistence
    seaice_res_persistence = evaluate_seaice_model(
        seaice_baseline,
        seaice_test,
        feature_cols=[],
        target_col="concentration",
        is_baseline=True
    )
    
    # 5. Sea-Ice XGBoost
    seaice_res_xgb = None
    if seaice_xgb_model is not None:
        try:
            seaice_xgb_test = seaice_test.dropna(subset=["lag_1"])
            from ml.training.seaice_train import build_features
            seaice_xgb_test_feats = build_features(seaice_test)
            seaice_res_xgb = evaluate_seaice_model(
                seaice_xgb_model,
                seaice_xgb_test_feats,
                feature_cols=["lag_1", "lag_2", "lag_3", "day_of_year", "lat", "lon"],
                target_col="concentration",
                is_baseline=False
            )
        except Exception as e:
            print(f"Error evaluating Sea-Ice XGBoost: {e}")
    
    # 6. Sea-Ice ConvLSTM
    # The ConvLSTM outputs a sequence of grids. We need to flatten the grids to match the aligned df.
    class FlattenedConvLSTM:
        def __init__(self, model, seq_len=5):
            self.model = model
            self.seq_len = seq_len
            self.model.eval()
        def predict(self, df):
            # df is aligned_seaice_test, but we need the original df to build grids
            grid_seq = dataframe_to_grid_sequence(seaice_test)
            X, _ = make_seaice_sequences(grid_seq, input_len=self.seq_len)
            X_t = torch.tensor(X).unsqueeze(2)
            with torch.no_grad():
                preds = self.model(X_t).numpy() # Shape: (time, rows, cols)
            
            # Flatten predictions to match aligned_seaice_test
            flat_preds = []
            dates = sorted(seaice_test["date"].unique())[self.seq_len:]
            for t_idx, date in enumerate(dates):
                # The dataframe is sorted by date, row, col
                date_df = aligned_seaice_test[aligned_seaice_test["date"] == date].sort_values(["row", "col"])
                for _, r in date_df.iterrows():
                    flat_preds.append(preds[t_idx, int(r["row"]), int(r["col"])])
            return np.array(flat_preds)

    seaice_res_convlstm = None
    if seaice_convlstm_model is not None:
        try:
            aligned_seaice_test = get_aligned_seaice_df(seaice_test, seq_len=5)
            seaice_res_convlstm = evaluate_seaice_model(
                FlattenedConvLSTM(seaice_convlstm_model, seq_len=5),
                aligned_seaice_test,
                feature_cols=[],
                target_col="concentration",
                is_baseline=False
            )
        except Exception as e:
            print(f"Error evaluating Sea-Ice ConvLSTM: {e}")
    
    results = {
        "trajectory": {
            "persistence": traj_res_persistence,
            "xgboost": traj_res_xgb,
            "lstm": traj_res_lstm
        },
        "sea_ice": {
            "persistence": seaice_res_persistence,
            "xgboost": seaice_res_xgb,
            "convlstm": seaice_res_convlstm
        }
    }
    
    print("Generating report...")
    generate_report(results, report_dir="ml/benchmarks/reports")
    print("Done!")

if __name__ == "__main__":
    main()
