from pathlib import Path
from datetime import date, timedelta
import subprocess


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = BASE_DIR / "raw" / "nsidc" / "2026"

BASE_URL = (
    "https://noaadata.apps.nsidc.org/"
    "NOAA/G02202_V6/south/daily/2026"
)

START_DATE = date(2026, 1, 1)
END_DATE = date(2026, 6, 23)


# ---------------------------------------------------------
# Create output directory
# ---------------------------------------------------------

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Download function
# ---------------------------------------------------------

def download_file(file_date: date) -> bool:

    date_str = file_date.strftime("%Y%m%d")

    filename = f"sic_pss25_{date_str}_am2_v06r00.nc"

    url = f"{BASE_URL}/{filename}"

    output_file = OUTPUT_DIR / filename

    # Skip files already downloaded
    if output_file.exists() and output_file.stat().st_size > 0:
        print(f"[SKIP] {filename}")
        return True

    print(f"[DOWNLOAD] {filename}")

    result = subprocess.run(
        [
            "curl.exe",
            "-L",
            "--fail",
            "--retry",
            "3",
            "--retry-delay",
            "2",
            url,
            "-o",
            str(output_file),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print(f"[ERROR] Failed: {filename}")

        if result.stderr:
            print(result.stderr)

        if output_file.exists():
            output_file.unlink()

        return False

    if not output_file.exists() or output_file.stat().st_size == 0:
        print(f"[ERROR] Empty file: {filename}")

        if output_file.exists():
            output_file.unlink()

        return False

    print(
        f"[OK] {filename} "
        f"({output_file.stat().st_size / 1024:.1f} KB)"
    )

    return True


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

current_date = START_DATE

success = 0
failed = 0
total = 0

while current_date <= END_DATE:

    total += 1

    if download_file(current_date):
        success += 1
    else:
        failed += 1

    current_date += timedelta(days=1)


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

print("\n" + "=" * 50)
print("DOWNLOAD SUMMARY")
print("=" * 50)

print(f"Total files:      {total}")
print(f"Successful:       {success}")
print(f"Failed:           {failed}")
print(f"Output directory: {OUTPUT_DIR}")