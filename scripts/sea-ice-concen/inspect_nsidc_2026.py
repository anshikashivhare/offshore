import xarray as xr
from pathlib import Path

file = Path(
    "raw/nsidc/2026/"
    "sic_pss25_20260101_am2_v06r00.nc"
)

print(f"Opening: {file}")

ds = xr.open_dataset(file)

print("\n=== DATASET ===")
print(ds)

print("\n=== DIMENSIONS ===")
for name, size in ds.sizes.items():
    print(f"{name}: {size}")

print("\n=== VARIABLES ===")
for name in ds.data_vars:
    da = ds[name]

    print(f"\n{name}")
    print(f"  dimensions: {da.dims}")
    print(f"  dtype:      {da.dtype}")
    print(f"  units:      {da.attrs.get('units', 'N/A')}")

print("\n=== TIME ===")
if "time" in ds.coords:
    print(ds.time.values)

print("\n=== CRS ===")
if "crs" in ds:
    print(ds["crs"])
    print("CRS variable attributes:")
    for key, value in ds["crs"].attrs.items():
        print(f"  {key}: {value}")

print("\n=== SIC CHECK ===")

sic = ds["cdr_seaice_conc"]

print(f"Minimum: {float(sic.min()):.6f}")
print(f"Maximum: {float(sic.max()):.6f}")
print(f"Mean:    {float(sic.mean()):.6f}")

print("\n=== EXPECTED STRUCTURE CHECK ===")

checks = {
    "time dimension = 1": ds.sizes.get("time") == 1,
    "y dimension = 332": ds.sizes.get("y") == 332,
    "x dimension = 316": ds.sizes.get("x") == 316,
    "SIC variable exists": "cdr_seaice_conc" in ds,
    "QA variable exists": "cdr_seaice_conc_qa_flag" in ds,
}

for name, result in checks.items():
    print(f"{name}: {'PASS' if result else 'FAIL'}")

print("\nInspection complete.")

ds.close()