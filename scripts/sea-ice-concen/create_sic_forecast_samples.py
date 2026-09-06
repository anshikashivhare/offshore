from pathlib import Path
import numpy as np
import xarray as xr


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "processed"
    / "model_ready"
    / "sea_ice_2025.nc"
)

OUTPUT_FILE = (
    BASE_DIR
    / "processed"
    / "model_ready"
    / "sea_ice_forecast_samples_2025.nc"
)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

INPUT_DAYS = 7
FORECAST_DAYS = 1


# ---------------------------------------------------------
# Load dataset
# ---------------------------------------------------------

print("Opening dataset...")

ds = xr.open_dataset(INPUT_FILE)

sic = ds["sea_ice_concentration"]


# ---------------------------------------------------------
# Find valid consecutive windows
# ---------------------------------------------------------

times = ds["time"].values

samples_x = []
samples_y = []
sample_dates = []

for i in range(len(times) - INPUT_DAYS - FORECAST_DAYS + 1):

    input_times = times[i:i + INPUT_DAYS]
    target_time = times[i + INPUT_DAYS]

    # Check that all input dates are exactly one day apart
    input_diffs = np.diff(input_times).astype("timedelta64[D]")

    if not np.all(input_diffs == np.timedelta64(1, "D")):
        continue

    # Check target immediately follows the input window
    if target_time - input_times[-1] != np.timedelta64(1, "D"):
        continue

    samples_x.append(
        sic.isel(
            time=slice(i, i + INPUT_DAYS)
        ).values
    )

    samples_y.append(
        sic.isel(time=i + INPUT_DAYS).values
    )

    sample_dates.append(target_time)


# ---------------------------------------------------------
# Convert to arrays
# ---------------------------------------------------------

X = np.stack(samples_x)

Y = np.stack(samples_y)

sample_dates = np.asarray(sample_dates)


# ---------------------------------------------------------
# Create output dataset
# ---------------------------------------------------------

sample_ds = xr.Dataset(
    {
        "input_sea_ice_concentration": (
            ("sample", "input_day", "y", "x"),
            X
        ),

        "target_sea_ice_concentration": (
            ("sample", "y", "x"),
            Y
        ),
    },
    coords={
        "sample": np.arange(len(sample_dates)),
        "input_day": np.arange(INPUT_DAYS),
        "target_time": (
            "sample",
            sample_dates
        ),
        "x": ds["x"].values,
        "y": ds["y"].values,
    }
)


# ---------------------------------------------------------
# Metadata
# ---------------------------------------------------------

sample_ds.attrs["dataset_type"] = "forecast_samples"

sample_ds.attrs["source"] = (
    "NOAA/NSIDC CDR Passive Microwave "
    "Sea Ice Concentration Version 6"
)

sample_ds.attrs["input_window_days"] = INPUT_DAYS
sample_ds.attrs["forecast_horizon_days"] = FORECAST_DAYS

sample_ds.attrs["excluded_dates"] = (
    "2025-08-31, 2025-09-17, 2025-12-13"
)


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

print("\nSaving forecast samples...")

sample_ds.to_netcdf(
    OUTPUT_FILE,
    encoding={
        "input_sea_ice_concentration": {
            "zlib": True,
            "complevel": 4
        },
        "target_sea_ice_concentration": {
            "zlib": True,
            "complevel": 4
        }
    }
)


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("FORECAST SAMPLE DATASET CREATED")
print("=" * 60)

print(f"Samples: {len(sample_dates)}")
print(f"Input shape: {X.shape}")
print(f"Target shape: {Y.shape}")

if len(sample_dates) > 0:
    print(
        "First target:",
        str(sample_dates[0])[:10]
    )

    print(
        "Last target:",
        str(sample_dates[-1])[:10]
    )

print(f"Output: {OUTPUT_FILE}")