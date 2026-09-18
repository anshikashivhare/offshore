from pathlib import Path
import xarray as xr

BASE_DIR = Path(__file__).resolve().parent.parent
file = BASE_DIR / "raw" / "sic_pss25_20220101_F17_v06r00.nc"

ds = xr.open_dataset(file)

print(ds)
print("\n=== VARIABLES ===")
print(ds.data_vars)

print("\n=== COORDINATES ===")
print(ds.coords)

print("\n=== ATTRIBUTES ===")
for key, value in ds.attrs.items():
    print(f"{key}: {value}")

ds.close()