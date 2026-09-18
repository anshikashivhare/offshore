from pathlib import Path
import xarray as xr

DATA_DIR = Path("processed/nsidc/2026")

files = sorted(DATA_DIR.glob("*.nc"))

print("=" * 60)
print("NSIDC 2026 PROCESSED DATA VALIDATION")
print("=" * 60)

print(f"Processed files found: {len(files)}")

if not files:
    raise RuntimeError("No processed files found.")

expected_variables = {
    "sea_ice_concentration",
    "sea_ice_uncertainty",
    "qa_flag",
    "spatial_interpolation_flag",
    "temporal_interpolation_flag",
}

all_dimensions_ok = True
all_variables_ok = True
all_ranges_ok = True

for i, file in enumerate(files):

    with xr.open_dataset(file) as ds:

        dimensions_ok = (
            ds.sizes.get("time") == 1
            and ds.sizes.get("y") == 332
            and ds.sizes.get("x") == 316
        )

        variables_ok = expected_variables.issubset(ds.data_vars)

        sic = ds["sea_ice_concentration"]

        sic_min = float(sic.min())
        sic_max = float(sic.max())

        ranges_ok = (
            sic_min >= 0.0
            and sic_max <= 1.0
        )

        all_dimensions_ok &= dimensions_ok
        all_variables_ok &= variables_ok
        all_ranges_ok &= ranges_ok

        if i < 3 or i >= len(files) - 3:
            print(
                f"{file.name} | "
                f"dimensions={'PASS' if dimensions_ok else 'FAIL'} | "
                f"variables={'PASS' if variables_ok else 'FAIL'} | "
                f"SIC={sic_min:.4f}..{sic_max:.4f}"
            )

print("\n=== FINAL CHECKS ===")

checks = {
    "174 processed files": len(files) == 174,
    "dimensions correct": all_dimensions_ok,
    "variables correct": all_variables_ok,
    "SIC range 0-1": all_ranges_ok,
}

all_pass = True

for name, result in checks.items():
    print(f"{name}: {'PASS' if result else 'FAIL'}")
    if not result:
        all_pass = False

print(
    f"\nOverall validation: "
    f"{'PASS' if all_pass else 'FAIL'}"
)