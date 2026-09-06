import xarray as xr
from pathlib import Path

file_path = Path("raw/era5/era5_test_20250101_20250103.nc")

print(f"Opening: {file_path}")

ds = xr.open_dataset(file_path)

print("\n=== DATASET ===")
print(ds)

print("\n=== DIMENSIONS ===")
for name, size in ds.sizes.items():
    print(f"{name}: {size}")

print("\n=== VARIABLES ===")
for name in ds.data_vars:
    da = ds[name]
    print(f"{name}:")
    print(f"  dimensions: {da.dims}")
    print(f"  dtype:      {da.dtype}")
    print(f"  units:      {da.attrs.get('units', 'N/A')}")
    print(f"  long_name:  {da.attrs.get('long_name', 'N/A')}")

print("\n=== COORDINATES ===")
for name in ds.coords:
    values = ds[name].values
    print(f"{name}:")
    print(f"  shape: {values.shape}")
    print(f"  first: {values.flat[0]}")
    print(f"  last:  {values.flat[-1]}")

print("\n=== TIME ===")
if "time" in ds.coords:
    print(ds["time"].values)

print("\n=== LATITUDE ===")
if "latitude" in ds.coords:
    print(
        f"min={float(ds.latitude.min())}, "
        f"max={float(ds.latitude.max())}"
    )

print("\n=== LONGITUDE ===")
if "longitude" in ds.coords:
    print(
        f"min={float(ds.longitude.min())}, "
        f"max={float(ds.longitude.max())}"
    )

print("\n=== BASIC VALIDATION ===")

expected_variables = {
    "t2m",
    "u10",
    "v10",
    "sp",
}

actual_variables = set(ds.data_vars)

print("Expected variables present:",
      expected_variables.issubset(actual_variables))

print("Number of time steps:", ds.sizes.get("time", "N/A"))

print("\nInspection complete.")

ds.close()