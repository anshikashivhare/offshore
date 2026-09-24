import sys, os
import traceback

print("Testing ML Load...")
try:
    import xgboost as xgb
    print(f"XGBoost import: PASS (version {xgb.__version__})")
except Exception as e:
    print("XGBoost import: FAIL")
    print(traceback.format_exc())
    sys.exit(1)

artifact_path = "../ml/models/weights/seaice_xgb_latest.json"
if os.path.exists(artifact_path):
    print(f"Artifact exists: PASS ({artifact_path})")
else:
    print(f"Artifact exists: FAIL ({artifact_path})")
    sys.exit(1)

try:
    model = xgb.Booster()
    model.load_model(artifact_path)
    print("Artifact load: PASS")
except Exception as e:
    print("Artifact load: FAIL")
    print(traceback.format_exc())
    sys.exit(1)

print("Diagnostic complete.")
