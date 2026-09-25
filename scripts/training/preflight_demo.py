import sys
import os
from pathlib import Path

def run_preflight():
    print("--- DEMO PREFLIGHT ---")
    warnings = 0
    errors = 0
    
    # Check paths
    base = Path(__file__).resolve().parents[2]
    models = base / "ml" / "models" / "weights"
    if not (models / "seaice_xgb_v002.json").exists():
        print("[FAIL] XGBoost Sea-Ice model missing.")
        errors += 1
    else:
        print("[PASS] XGBoost Sea-Ice model found.")
        
    if not (models / "iceberg_lstm_v002.pt").exists():
        print("[FAIL] LSTM Iceberg model missing.")
        errors += 1
    else:
        print("[PASS] LSTM Iceberg model found.")

    # Check env
    demo_mode = os.environ.get("DEMO_MODE", "True")
    if demo_mode.lower() in ("true", "1", "yes"):
        print("[WARNING] DEMO_MODE is active (Synthetic fallbacks enabled).")
        warnings += 1
        
    print(f"Preflight finished: {errors} errors, {warnings} warnings.")
    if errors > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    run_preflight()
