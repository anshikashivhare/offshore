import xarray as xr
from pathlib import Path


DATA_DIR = Path("raw/copernicus_marine/2026")

files = sorted(DATA_DIR.glob("*.nc"))

print("=" * 70)
print("COPERNICUS MARINE 2026 VALIDATION")
print("=" * 70)

print(f"Files found: {len(files)}")

all_times = []

for file in files:

    with xr.open_dataset(file) as ds:

        times = ds["time"].values

        print(
            f"{file.name} | "
            f"{str(times[0])[:10]} -> "
            f"{str(times[-1])[:10]} | "
            f"days={len(times)}"
        )

        all_times.extend(times)


all_times = sorted(all_times)

print("\n=== OVERALL ===")

print(f"First date: {str(all_times[0])[:10]}")
print(f"Last date:  {str(all_times[-1])[:10]}")
print(f"Total records: {len(all_times)}")
print(f"Unique dates: {len(set(all_times))}")

expected_start = "2026-01-01"
expected_end = "2026-06-23"

print("\n=== CHECKS ===")

checks = {
    "6 monthly files": len(files) == 6,
    "correct first date": str(all_times[0])[:10] == expected_start,
    "correct last date": str(all_times[-1])[:10] == expected_end,
    "174 unique days": len(set(all_times)) == 174,
}

all_pass = True

for name, result in checks.items():
    print(f"{name}: {'PASS' if result else 'FAIL'}")
    all_pass &= result

print(
    f"\nOverall validation: "
    f"{'PASS' if all_pass else 'FAIL'}"
)