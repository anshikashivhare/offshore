"""
Retraining Trigger

This script checks the model performance trends using the monitor layer.
If a model's performance trend is flagged as "degrading", it automatically
triggers the corresponding training script to attempt to improve the model
using the latest data/hyperparameters.

Run: python -m mlops.retrain_trigger
"""

import subprocess
from mlops.monitor import PRIMARY_METRIC, summarize

TRAINING_SCRIPTS = {
    "seaice_xgboost": ["python", "-m", "ml.training.seaice_train"],
    "seaice_convlstm": ["python", "-m", "ml.training.seaice_train_convlstm"],
    "trajectory_xgboost": ["python", "-m", "ml.training.trajectory_train"],
    "trajectory_lstm": ["python", "-m", "ml.training.trajectory_train_lstm"],
}


def trigger_retraining():
    print("=" * 70)
    print("AUTOMATED RETRAINING TRIGGER")
    print("=" * 70)
    
    for model_name in PRIMARY_METRIC:
        summary = summarize(model_name)
        trend = summary.get("trend", "")
        
        print(f"\nChecking [{model_name}]...")
        if trend.startswith("degrading"):
            print(f"  [!] Trend is '{trend}'. Triggering retraining...")
            script_cmd = TRAINING_SCRIPTS.get(model_name)
            if not script_cmd:
                print(f"  [-] No training script mapped for {model_name}.")
                continue
                
            print(f"  [>] Running: {' '.join(script_cmd)}")
            try:
                result = subprocess.run(script_cmd, capture_output=True, text=True, check=True)
                print(f"  [+] Retraining completed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"  [x] Retraining failed with exit code {e.returncode}.")
                print(f"  [x] Error output: {e.stderr.strip()}")
        else:
            print(f"  [-] Trend is '{trend}'. No retraining required.")

if __name__ == "__main__":
    trigger_retraining()
