import xarray as xr
from pathlib import Path

INPUT_DIR = Path("raw/era5/2026/extracted/Q2")
OUTPUT_DIR = Path("processed/era5/2026/Q2")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=== TRIMMING ERA5 2026 Q2 ===")
print("Keeping: 2026-04-01 → 2026-06-23")

for file in sorted(INPUT_DIR.glob("*.nc")):

    print(f"\nProcessing: {file.name}")

    with xr.open_dataset(file) as ds:

        trimmed = ds.sel(
            valid_time=slice("2026-04-01", "2026-06-23")
        )

        output_file = OUTPUT_DIR / file.name

        trimmed.to_netcdf(output_file)

        print(
            f"Saved: {output_file.name} | "
            f"days={trimmed.sizes['valid_time']}"
        )

print("\nTrimming complete.")