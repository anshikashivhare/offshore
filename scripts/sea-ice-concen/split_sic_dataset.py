from pathlib import Path
import json
import xarray as xr


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "processed"
    / "model_ready"
    / "sea_ice_forecast_samples_2025.nc"
)

OUTPUT_DIR = (
    BASE_DIR
    / "processed"
    / "model_ready"
    / "splits"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Load dataset
# ---------------------------------------------------------

print("Opening forecast sample dataset...")

ds = xr.open_dataset(INPUT_FILE)

n = ds.sizes["sample"]

print(f"Total samples: {n}")


# ---------------------------------------------------------
# Chronological split
# ---------------------------------------------------------

train_end = int(n * 0.70)
val_end = int(n * 0.85)

train = ds.isel(
    sample=slice(0, train_end)
)

validation = ds.isel(
    sample=slice(train_end, val_end)
)

test = ds.isel(
    sample=slice(val_end, n)
)


# ---------------------------------------------------------
# Save splits
# ---------------------------------------------------------

print("\nSaving splits...")

train.to_netcdf(
    OUTPUT_DIR / "train.nc"
)

validation.to_netcdf(
    OUTPUT_DIR / "validation.nc"
)

test.to_netcdf(
    OUTPUT_DIR / "test.nc"
)


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

summary = {
    "total_samples": n,
    "train_samples": train.sizes["sample"],
    "validation_samples": validation.sizes["sample"],
    "test_samples": test.sizes["sample"],

    "train_start": str(
        train["target_time"].values[0]
    )[:10],

    "train_end": str(
        train["target_time"].values[-1]
    )[:10],

    "validation_start": str(
        validation["target_time"].values[0]
    )[:10],

    "validation_end": str(
        validation["target_time"].values[-1]
    )[:10],

    "test_start": str(
        test["target_time"].values[0]
    )[:10],

    "test_end": str(
        test["target_time"].values[-1]
    )[:10],
}


with open(
    OUTPUT_DIR / "split_summary.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        summary,
        f,
        indent=4
    )


# ---------------------------------------------------------
# Print summary
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("DATASET SPLIT COMPLETE")
print("=" * 60)

print(f"Train:       {summary['train_samples']}")
print(
    f"  {summary['train_start']} → "
    f"{summary['train_end']}"
)

print(f"\nValidation:  {summary['validation_samples']}")
print(
    f"  {summary['validation_start']} → "
    f"{summary['validation_end']}"
)

print(f"\nTest:        {summary['test_samples']}")
print(
    f"  {summary['test_start']} → "
    f"{summary['test_end']}"
)

print(f"\nOutput: {OUTPUT_DIR}")