from pathlib import Path
from datetime import date, timedelta


DATA_DIR = Path("raw/nsidc/2026")

START_DATE = date(2026, 1, 1)
END_DATE = date(2026, 6, 23)


expected_dates = []
current = START_DATE

while current <= END_DATE:
    expected_dates.append(current)
    current += timedelta(days=1)


print("=== NSIDC 2026 VALIDATION ===")
print(f"Expected files: {len(expected_dates)}")
print(f"Directory: {DATA_DIR}")

missing = []
empty = []
found_dates = []

for d in expected_dates:

    date_str = d.strftime("%Y%m%d")

    filename = f"sic_pss25_{date_str}_am2_v06r00.nc"
    path = DATA_DIR / filename

    if not path.exists():
        missing.append(filename)
        continue

    size = path.stat().st_size

    if size == 0:
        empty.append(filename)
        continue

    found_dates.append(d)


print("\n=== RESULTS ===")
print(f"Files found:   {len(found_dates)}")
print(f"Missing:       {len(missing)}")
print(f"Empty:         {len(empty)}")

if found_dates:
    print(f"First file:    {found_dates[0]}")
    print(f"Last file:     {found_dates[-1]}")


if missing:
    print("\n=== MISSING FILES ===")
    for filename in missing:
        print(filename)


if empty:
    print("\n=== EMPTY FILES ===")
    for filename in empty:
        print(filename)


print("\n=== VALIDATION ===")

checks = {
    "174 files present": len(found_dates) == 174,
    "no missing files": len(missing) == 0,
    "no empty files": len(empty) == 0,
    "first date correct": found_dates[0] == START_DATE if found_dates else False,
    "last date correct": found_dates[-1] == END_DATE if found_dates else False,
}

all_pass = True

for name, result in checks.items():
    print(f"{name}: {'PASS' if result else 'FAIL'}")
    if not result:
        all_pass = False


print(f"\nOverall validation: {'PASS' if all_pass else 'FAIL'}")