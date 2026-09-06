from pathlib import Path
import numpy as np
import xarray as xr

BASE_DIR = Path(__file__).resolve().parent.parent
FILE = BASE_DIR / "processed" / "sea_ice_20220101_processed.nc"

ds = xr.open_dataset(FILE)

sic = ds["sea_ice_concentration"]
uncertainty = ds["sea_ice_uncertainty"]
qa = ds["qa_flag"]

total = sic.size
nan_count = int(sic.isnull().sum())
valid_count = total - nan_count

print("========== SEA ICE QC REPORT ==========")
print(f"Total grid cells:       {total}")
print(f"Valid SIC cells:        {valid_count}")
print(f"NaN cells:              {nan_count}")
print(f"NaN percentage:         {nan_count / total * 100:.2f}%")

print("\n--- SIC ---")
print(f"Minimum: {float(sic.min(skipna=True)):.4f}")
print(f"Maximum: {float(sic.max(skipna=True)):.4f}")
print(f"Mean:    {float(sic.mean(skipna=True)):.4f}")
print(f"Median:  {float(sic.median(skipna=True)):.4f}")

print("\n--- UNCERTAINTY ---")
print(f"Minimum: {float(uncertainty.min(skipna=True)):.4f}")
print(f"Maximum: {float(uncertainty.max(skipna=True)):.4f}")
print(f"Mean:    {float(uncertainty.mean(skipna=True)):.4f}")

print("\n--- QA FLAGS ---")
qa_values, qa_counts = np.unique(qa.values, return_counts=True)

for value, count in zip(qa_values, qa_counts):
    print(f"QA {int(value):3d}: {int(count):6d} cells")

print("\n--- COORDINATES ---")
print(f"X range: {float(ds.x.min())} to {float(ds.x.max())}")
print(f"Y range: {float(ds.y.min())} to {float(ds.y.max())}")

print("\n--- TIME ---")
print(ds.time.values)

ds.close()