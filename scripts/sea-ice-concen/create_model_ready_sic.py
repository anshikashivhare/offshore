from pathlib import Path
import xarray as xr


BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_DIR = BASE_DIR / "processed" / "nsidc" / "2025"

OUTPUT_FILE = (
    BASE_DIR
    / "processed"
    / "model_ready"
    / "sea_ice_2025.nc"
)


# Dates excluded during prototype QC
EXCLUDED_DATES = {
    "2025-08-31",
    "2025-09-17",
    "2025-12-13",
}


# ---------------------------------------------------------
# Find input files
# ---------------------------------------------------------

files = sorted(INPUT_DIR.glob("*.nc"))

print("=" * 60)
print("CREATE MODEL-READY SEA-ICE DATASET")
print("=" * 60)

print(f"Input files found: {len(files)}")


# ---------------------------------------------------------
# Remove excluded dates
# ---------------------------------------------------------

usable_files = []

for file in files:

    date_str = file.name.split("_")[2]

    if date_str in {
        d.replace("-", "")
        for d in EXCLUDED_DATES
    }:
        print(f"[EXCLUDE] {file.name}")
    else:
        usable_files.append(file)


print(f"\nUsable files: {len(usable_files)}")


# ---------------------------------------------------------
# Open and combine
# ---------------------------------------------------------

print("\nCombining datasets...")

datasets = []

for file in usable_files:

    ds = xr.open_dataset(file)

    # Keep only variables needed by the model/data pipeline
    ds = ds[
        [
            "sea_ice_concentration",
            "sea_ice_uncertainty",
            "qa_flag",
            "spatial_interpolation_flag",
            "temporal_interpolation_flag",
        ]
    ]

    datasets.append(ds)


combined = xr.concat(
    datasets,
    dim="time"
)


# ---------------------------------------------------------
# Sort by time
# ---------------------------------------------------------

combined = combined.sortby("time")


# ---------------------------------------------------------
# Add metadata
# ---------------------------------------------------------

combined.attrs["dataset_type"] = "model_ready"
combined.attrs["prototype_period"] = "2025"
combined.attrs["excluded_dates"] = (
    "2025-08-31, 2025-09-17, 2025-12-13"
)
combined.attrs["source"] = (
    "NOAA/NSIDC CDR Passive Microwave Sea Ice "
    "Concentration Version 6"
)


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

encoding = {
    variable: {
        "zlib": True,
        "complevel": 4
    }
    for variable in combined.data_vars
}


print("\nSaving...")

combined.to_netcdf(
    OUTPUT_FILE,
    encoding=encoding
)


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("MODEL-READY DATASET CREATED")
print("=" * 60)

print(f"Output: {OUTPUT_FILE}")
print(f"Time steps: {combined.sizes['time']}")
print(f"Grid: {combined.sizes['y']} x {combined.sizes['x']}")
print(
    f"Date range: "
    f"{str(combined.time.values[0])[:10]} → "
    f"{str(combined.time.values[-1])[:10]}"
)