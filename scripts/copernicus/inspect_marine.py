import xarray as xr
from pathlib import Path


FILES = [
    Path("raw/copernicus_marine/2025/copernicus_marine_2025.nc"),
    Path("raw/copernicus_marine/2026/copernicus_marine_2026_01.nc"),
]


for file in FILES:

    print("\n" + "=" * 70)
    print(f"FILE: {file}")
    print("=" * 70)

    with xr.open_dataset(file) as ds:

        print("\nDATASET:")
        print(ds)

        print("\nVARIABLES:")
        for name in ds.data_vars:
            da = ds[name]
            print(
                f"  {name}: "
                f"dims={da.dims}, "
                f"dtype={da.dtype}, "
                f"units={da.attrs.get('units', 'N/A')}"
            )

        print("\nDIMENSIONS:")
        for name, size in ds.sizes.items():
            print(f"  {name}: {size}")

        print("\nCOORDINATES:")
        for name in ds.coords:
            da = ds[name]
            print(
                f"  {name}: "
                f"dims={da.dims}, "
                f"size={da.size}"
            )

        print("\nTIME:")
        for candidate in ["time", "valid_time"]:
            if candidate in ds.coords:
                values = ds[candidate].values
                print(f"  {candidate}:")
                print(f"    first = {values[0]}")
                print(f"    last  = {values[-1]}")
                print(f"    count = {len(values)}")

        print("\nDEPTH:")
        for candidate in ["depth", "deptht", "depthu", "depthv"]:
            if candidate in ds.coords:
                values = ds[candidate].values
                print(f"  {candidate}:")
                print(f"    first = {values[0]}")
                print(f"    last  = {values[-1]}")
                print(f"    count = {len(values)}")

        print("\nDATASET INSPECTION COMPLETE")