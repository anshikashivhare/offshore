import pandas as pd
from pathlib import Path
import json
import datetime

data_dir = Path("ml/data/raw")
manifest = {"datasets": []}

for file in data_dir.glob("*.csv"):
    df = pd.read_csv(file, nrows=100) # Read sample for fast profiling
    
    # Check if there are any time-like columns
    time_cols = [c for c in df.columns if 'time' in c.lower() or 'date' in c.lower()]
    
    dataset_info = {
        "dataset_id": file.stem,
        "filename": file.name,
        "format": "csv",
        "size_bytes": file.stat().st_size,
        "source": "Provided by user (synthetic 2026)",
        "synthetic_or_real": "SYNTHETIC" if "synthetic" in file.name.lower() else "REAL",
        "variables": list(df.columns),
        "spatial_columns": [c for c in df.columns if c.lower() in ['lat', 'latitude', 'lon', 'longitude']],
        "temporal_columns": time_cols,
        "processing_status": "PROFILED",
        "quality_status": "PENDING"
    }
    manifest["datasets"].append(dataset_info)

with open("ml/datasets/dataset_manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)

print("Profiled datasets:")
for ds in manifest["datasets"]:
    print(f"- {ds['filename']} ({ds['size_bytes']} bytes, {len(ds['variables'])} vars)")
