import xarray as xr
from pathlib import Path

BASE = Path("raw/era5/2026/extracted")

expected = {
    "Q1": ("2026-01-01", "2026-03-31"),
    "Q2": ("2026-04-01", "2026-06-23"),
}

variables = {"t2m", "u10", "v10", "sp"}

print("=" * 70)
print("ERA5 2026 VALIDATION")
print("=" * 70)

all_pass = True

for quarter, (expected_first, expected_last) in expected.items():

    print(f"\n=== {quarter} ===")

    files = sorted((BASE / quarter).glob("*.nc"))

    if len(files) != 4:
        print(f"ERROR: expected 4 files, found {len(files)}")
        all_pass = False
        continue

    times_by_var = {}

    for file in files:

        with xr.open_dataset(file) as ds:

            var_names = set(ds.data_vars)

            var = next(iter(var_names))
            times = ds["valid_time"].values

            first = str(times[0])[:10]
            last = str(times[-1])[:10]
            count = len(times)

            units = ds[var].attrs.get("units", "N/A")

            print(
                f"{var:4s} | "
                f"{first} -> {last} | "
                f"days={count} | "
                f"units={units}"
            )

            if first != expected_first:
                all_pass = False

            if quarter == "Q1":
                expected_days = 90
            else:
                expected_days = 84   # Apr 1 -> Jun 23

            if count != expected_days:
                all_pass = False

            times_by_var[var] = times

    if set(times_by_var) != variables:
        print("ERROR: variable set is incorrect.")
        all_pass = False

    # Check that all variables have identical timestamps
    time_lists = list(times_by_var.values())

    if time_lists:
        reference = time_lists[0]

        for times in time_lists[1:]:
            if not (times == reference).all():
                print("ERROR: timestamps differ between variables.")
                all_pass = False

print("\n" + "=" * 70)
print("FINAL RESULT")
print("=" * 70)

print(f"ERA5 2026 validation: {'PASS' if all_pass else 'FAIL'}")