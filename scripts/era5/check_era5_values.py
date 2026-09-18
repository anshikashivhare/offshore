import xarray as xr
from pathlib import Path

folder = Path("raw/era5/era5_test_20250101_20250103.nc")

print("=== ERA5 VALUE CHECK ===")

for file in sorted(folder.glob("*.nc")):
    print(f"\n=== {file.name} ===")

    ds = xr.open_dataset(file)

    for var in ds.data_vars:
        da = ds[var]

        print(f"Variable : {var}")
        print(f"Units    : {da.attrs.get('units', 'N/A')}")
        print(f"Min      : {float(da.min()):.4f}")
        print(f"Max      : {float(da.max()):.4f}")
        print(f"Mean     : {float(da.mean()):.4f}")

    ds.close()

print("\nValue check complete.")