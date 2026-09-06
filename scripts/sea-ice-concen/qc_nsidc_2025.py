from pathlib import Path
from datetime import date, timedelta
import re

import numpy as np
import xarray as xr


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "processed" / "nsidc" / "2025"


# ---------------------------------------------------------
# Find files
# ---------------------------------------------------------

files = sorted(DATA_DIR.glob("*.nc"))

print("=" * 60)
print("NSIDC 2025 TIME-SERIES QC")
print("=" * 60)

print(f"Files found: {len(files)}")


# ---------------------------------------------------------
# Extract dates from filenames
# ---------------------------------------------------------

pattern = re.compile(r"sic_pss25_(\d{8})_am2_v06r00\.nc")

file_dates = []

for file in files:

    match = pattern.fullmatch(file.name)

    if not match:
        print(f"[WARNING] Unexpected filename: {file.name}")
        continue

    date_value = date.fromisoformat(
        match.group(1)[:4]
        + "-"
        + match.group(1)[4:6]
        + "-"
        + match.group(1)[6:8]
    )

    file_dates.append(date_value)


# ---------------------------------------------------------
# Sort dates
# ---------------------------------------------------------

file_dates = sorted(file_dates)


# ---------------------------------------------------------
# Date continuity
# ---------------------------------------------------------

print("\n=== DATE COVERAGE ===")

if file_dates:
    print(f"First date: {file_dates[0]}")
    print(f"Last date:  {file_dates[-1]}")

expected_dates = []

current = date(2025, 1, 1)
end = date(2025, 12, 31)

while current <= end:
    expected_dates.append(current)
    current += timedelta(days=1)


missing_dates = sorted(
    set(expected_dates) - set(file_dates)
)

duplicate_dates = sorted(
    {
        d
        for d in file_dates
        if file_dates.count(d) > 1
    }
)


print(f"Expected dates: {len(expected_dates)}")
print(f"Actual dates:   {len(file_dates)}")
print(f"Missing dates:  {len(missing_dates)}")
print(f"Duplicate dates:{len(duplicate_dates)}")

if missing_dates:
    print("\nMissing:")
    for d in missing_dates:
        print(" ", d)

if duplicate_dates:
    print("\nDuplicates:")
    for d in duplicate_dates:
        print(" ", d)


# ---------------------------------------------------------
# Inspect every processed file
# ---------------------------------------------------------

print("\n=== DATA QC ===")

records = []

for index, file in enumerate(files, start=1):

    try:

        with xr.open_dataset(file) as ds:

            sic = ds["sea_ice_concentration"]

            values = sic.values

            finite = np.isfinite(values)

            valid_count = int(finite.sum())
            total_count = int(values.size)

            valid_fraction = (
                valid_count / total_count
                if total_count
                else 0
            )

            if valid_count > 0:

                valid_values = values[finite]

                sic_min = float(valid_values.min())
                sic_max = float(valid_values.max())
                sic_mean = float(valid_values.mean())

            else:

                sic_min = np.nan
                sic_max = np.nan
                sic_mean = np.nan

            records.append(
                {
                    "date": str(ds["time"].values[0])[:10],
                    "valid_cells": valid_count,
                    "valid_fraction": valid_fraction,
                    "sic_min": sic_min,
                    "sic_max": sic_max,
                    "sic_mean": sic_mean,
                }
            )

        if index % 25 == 0:
            print(f"Checked {index}/{len(files)} files")

    except Exception as exc:

        print(f"[ERROR] {file.name}")
        print(f"        {exc}")


# ---------------------------------------------------------
# Statistics
# ---------------------------------------------------------

print("\n=== SERIES STATISTICS ===")

valid_fractions = np.array(
    [r["valid_fraction"] for r in records]
)

means = np.array(
    [r["sic_mean"] for r in records]
)

print(
    f"Valid coverage min:  {valid_fractions.min():.4f}"
)

print(
    f"Valid coverage max:  {valid_fractions.max():.4f}"
)

print(
    f"Valid coverage mean: {valid_fractions.mean():.4f}"
)

print(
    f"SIC mean min:        {means.min():.4f}"
)

print(
    f"SIC mean max:        {means.max():.4f}"
)

print(
    f"SIC mean average:    {means.mean():.4f}"
)


# ---------------------------------------------------------
# Identify unusual coverage
# ---------------------------------------------------------

print("\n=== POTENTIAL OUTLIERS ===")

coverage_mean = valid_fractions.mean()
coverage_std = valid_fractions.std()

low_threshold = coverage_mean - 3 * coverage_std
high_threshold = coverage_mean + 3 * coverage_std


for record in records:

    coverage = record["valid_fraction"]

    if coverage < low_threshold or coverage > high_threshold:

        print(
            f"Coverage outlier: "
            f"{record['date']} "
            f"({coverage:.4f})"
        )


# ---------------------------------------------------------
# Identify impossible SIC values
# ---------------------------------------------------------

print("\n=== RANGE VALIDATION ===")

range_errors = []

for record in records:

    if (
        record["sic_min"] < 0
        or record["sic_max"] > 1
    ):
        range_errors.append(record["date"])


print(f"Range errors: {len(range_errors)}")

if range_errors:
    for d in range_errors:
        print(" ", d)


# ---------------------------------------------------------
# Final result
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("QC COMPLETE")
print("=" * 60)