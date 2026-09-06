import xarray as xr
from pathlib import Path

base = Path("raw/era5/2025/extracted")

expected = {
    "Q1": ("2025-01-01", "2025-03-31", 90),
    "Q2": ("2025-04-01", "2025-06-30", 91),
    "Q3": ("2025-07-01", "2025-09-30", 92),
    "Q4": ("2025-10-01", "2025-12-31", 92),
}

quarter_dirs = ["Q1", "Q2", "Q3", "Q4"]

for quarter in quarter_dirs:
    print(f"\n=== {quarter} ===")

    files = sorted((base / quarter).glob("*.nc"))

    if len(files) != 4:
        print(f"WARNING: Expected 4 files, found {len(files)}")

    all_ok = True

    for file in files:
        ds = xr.open_dataset(file)

        var = list(ds.data_vars)[0]

        times = ds["valid_time"].values
        first = str(times[0])[:10]
        last = str(times[-1])[:10]
        count = len(times)

        exp_first, exp_last, exp_count = expected[quarter]

        ok = (
            first == exp_first
            and last == exp_last
            and count == exp_count
        )

        print(
            f"{var:4s} | "
            f"{first} -> {last} | "
            f"days={count} | "
            f"{'OK' if ok else 'CHECK'}"
        )

        if not ok:
            all_ok = False

        ds.close()

    print(f"{quarter} validation: {'PASS' if all_ok else 'CHECK REQUIRED'}")

print("\nValidation complete.")