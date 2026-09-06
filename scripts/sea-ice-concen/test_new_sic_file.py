import xarray as xr
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

FILE = (
    BASE_DIR
    / "raw"
    / "nsidc"
    / "2025"
    / "sic_pss25_20250101_am2_v06r00.nc"
)

print(f"Opening: {FILE}")

with xr.open_dataset(FILE) as ds:
    print("\nDataset:")
    print(ds)

    print("\nDimensions:")
    print(ds.dims)

    print("\nVariables:")
    print(list(ds.data_vars))

    print("\nTime:")
    print(ds["time"].values)

    print("\nCRS/grid mapping:")
    if "crs" in ds:
        print(ds["crs"])


print("\nSUCCESS: file opened correctly.")