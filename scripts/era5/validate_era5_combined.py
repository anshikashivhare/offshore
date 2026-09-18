import xarray as xr
from pathlib import Path

file = Path("processed/era5/era5_2025.nc")

print(f"Opening: {file}")

ds = xr.open_dataset(file)

print("\n=== DATASET ===")
print(ds)

print("\n=== DIMENSIONS ===")
for name, size in ds.sizes.items():
    print(f"{name}: {size}")

print("\n=== TIME CHECK ===")
times = ds.time.values

print(f"First date: {times[0]}")
print(f"Last date:  {times[-1]}")
print(f"Number of dates: {len(times)}")

unique_times = len(set(times))

print(f"Unique dates: {unique_times}")
print(f"Duplicate dates: {len(times) - unique_times}")

print("\n=== SPATIAL CHECK ===")
print(f"Latitude:  {float(ds.latitude.min())} -> {float(ds.latitude.max())}")
print(f"Longitude: {float(ds.longitude.min())} -> {float(ds.longitude.max())}")

print("\n=== VARIABLES ===")
expected = ["t2m", "u10", "v10", "sp"]

for var in expected:
    if var in ds:
        da = ds[var]

        print(f"\n{var}")
        print(f"  dimensions: {da.dims}")
        print(f"  dtype:      {da.dtype}")
        print(f"  units:      {da.attrs.get('units', 'N/A')}")
        print(f"  min:        {float(da.min()):.4f}")
        print(f"  max:        {float(da.max()):.4f}")
        print(f"  mean:       {float(da.mean()):.4f}")
    else:
        print(f"\nMISSING: {var}")

print("\n=== FINAL VALIDATION ===")

checks = {
    "365 time steps": len(times) == 365,
    "correct first date": str(times[0])[:10] == "2025-01-01",
    "correct last date": str(times[-1])[:10] == "2025-12-31",
    "no duplicate dates": unique_times == 365,
    "161 latitude cells": ds.sizes.get("latitude") == 161,
    "1440 longitude cells": ds.sizes.get("longitude") == 1440,
    "all variables present": all(v in ds for v in expected),
}

for name, result in checks.items():
    print(f"{name}: {'PASS' if result else 'FAIL'}")

print("\nValidation complete.")

ds.close()