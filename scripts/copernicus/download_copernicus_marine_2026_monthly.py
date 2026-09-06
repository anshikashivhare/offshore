from pathlib import Path
from datetime import date, timedelta
import calendar
import copernicusmarine


# ============================================================
# Copernicus Marine - 2026 Monthly Downloader
# ============================================================

DATASET_ID = "cmems_mod_glo_phy_my_0.083deg_P1D-m"

# ------------------------------------------------------------
# Output directory
# ------------------------------------------------------------
OUTPUT_DIR = Path(r"raw\copernicus_marine\2026")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# Spatial region
# ------------------------------------------------------------
WEST = -180
EAST = 180
SOUTH = -80
NORTH = -50

# ------------------------------------------------------------
# Shallowest available depth
# ------------------------------------------------------------
DEPTH = 0.494025

# ------------------------------------------------------------
# Variables
# ------------------------------------------------------------
VARIABLES = [
    "uo",
    "vo",
    "thetao",
]

# ------------------------------------------------------------
# 2026 available period
# ------------------------------------------------------------
START_YEAR = 2026
START_MONTH = 1

END_YEAR = 2026
END_MONTH = 6
END_DAY = 23


def last_day_of_month(year, month):
    return calendar.monthrange(year, month)[1]


def month_end_date(year, month):
    last_day = last_day_of_month(year, month)

    # Dataset is currently available only through June 23, 2026
    if year == END_YEAR and month == END_MONTH:
        last_day = min(last_day, END_DAY)

    return date(year, month, last_day)


def download_month(year, month):
    start_date = date(year, month, 1)
    end_date = month_end_date(year, month)

    start_str = start_date.isoformat()
    end_str = end_date.isoformat()

    output_file = (
        OUTPUT_DIR
        / f"copernicus_marine_{year}_{month:02d}.nc"
    )

    print("\n" + "=" * 70)
    print(f"Downloading {year}-{month:02d}")
    print("=" * 70)

    print(f"Start date : {start_str}")
    print(f"End date   : {end_str}")
    print(f"Output     : {output_file}")
    print("=" * 70)

    # Skip a month if it already exists
    if output_file.exists():
        print("File already exists. Skipping.")
        return

    try:
        copernicusmarine.subset(
            dataset_id=DATASET_ID,
            variables=VARIABLES,
            start_datetime=start_str,
            end_datetime=end_str,
            minimum_longitude=WEST,
            maximum_longitude=EAST,
            minimum_latitude=SOUTH,
            maximum_latitude=NORTH,
            minimum_depth=DEPTH,
            maximum_depth=DEPTH,
            output_directory=str(OUTPUT_DIR),
            output_filename=output_file.name,
            force_download=False,
        )

        if output_file.exists():
            size_gb = output_file.stat().st_size / (1024 ** 3)

            print("\nDownload successful.")
            print(f"File: {output_file}")
            print(f"Size: {size_gb:.2f} GB")
        else:
            print("\nWARNING: Expected output file was not found.")

    except Exception as e:
        print("\nDOWNLOAD FAILED")
        print(f"Month : {year}-{month:02d}")
        print(f"Error : {e}")
        raise


def main():
    print("=" * 70)
    print("COPERNICUS MARINE 2026 MONTHLY DOWNLOAD")
    print("=" * 70)
    print(f"Region     : Lon {WEST} to {EAST}")
    print(f"             Lat {SOUTH} to {NORTH}")
    print(f"Depth      : {DEPTH} m")
    print(f"Variables  : {VARIABLES}")
    print("Period     : 2026-01-01 to 2026-06-23")
    print(f"Output dir : {OUTPUT_DIR}")
    print("=" * 70)

    current_year = START_YEAR
    current_month = START_MONTH

    while True:
        download_month(current_year, current_month)

        if (
            current_year == END_YEAR
            and current_month == END_MONTH
        ):
            break

        current_month += 1

        if current_month > 12:
            current_month = 1
            current_year += 1

    print("\n" + "=" * 70)
    print("ALL 2026 MONTHS COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()