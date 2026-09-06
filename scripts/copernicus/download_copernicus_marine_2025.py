from pathlib import Path
import copernicusmarine


# ============================================================
# Copernicus Marine - 2025 Download
# ============================================================

DATASET_ID = "cmems_mod_glo_phy_my_0.083deg_P1D-m"

# Output location
OUTPUT_DIR = Path(r"raw\copernicus_marine\2025")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# Time range
# ------------------------------------------------------------
START_DATE = "2025-01-01"
END_DATE = "2025-12-31"

# ------------------------------------------------------------
# Spatial region
# ------------------------------------------------------------
WEST = -180
EAST = 180
SOUTH = -80
NORTH = -50

# ------------------------------------------------------------
# Depth
# Shallowest available GLORYS depth level
# ------------------------------------------------------------
DEPTH = 0.494025

# ------------------------------------------------------------
# Variables
# ------------------------------------------------------------
VARIABLES = [
    "uo",       # Eastward sea water velocity
    "vo",       # Northward sea water velocity
    "thetao",   # Sea water potential temperature
]

# ------------------------------------------------------------
# Output file
# ------------------------------------------------------------
OUTPUT_FILE = OUTPUT_DIR / "copernicus_marine_2025.nc"


def main():
    print("=" * 60)
    print("Starting Copernicus Marine 2025 download")
    print("=" * 60)

    print(f"Dataset      : {DATASET_ID}")
    print(f"Start date   : {START_DATE}")
    print(f"End date     : {END_DATE}")
    print(f"Longitude    : {WEST} to {EAST}")
    print(f"Latitude     : {SOUTH} to {NORTH}")
    print(f"Depth        : {DEPTH} m")
    print(f"Variables    : {VARIABLES}")
    print(f"Output file  : {OUTPUT_FILE}")
    print("=" * 60)

    try:
        copernicusmarine.subset(
            dataset_id=DATASET_ID,
            variables=VARIABLES,
            start_datetime=START_DATE,
            end_datetime=END_DATE,
            minimum_longitude=WEST,
            maximum_longitude=EAST,
            minimum_latitude=SOUTH,
            maximum_latitude=NORTH,
            minimum_depth=DEPTH,
            maximum_depth=DEPTH,
            output_directory=str(OUTPUT_DIR),
            output_filename=OUTPUT_FILE.name,
            force_download=False,
        )

        print("\n" + "=" * 60)
        print("Download command completed successfully.")
        print("=" * 60)
        print(f"Expected output: {OUTPUT_FILE}")

        if OUTPUT_FILE.exists():
            size_gb = OUTPUT_FILE.stat().st_size / (1024 ** 3)
            print(f"File size      : {size_gb:.2f} GB")
        else:
            print("WARNING: Output file was not found at the expected path.")

    except Exception as e:
        print("\n" + "=" * 60)
        print("DOWNLOAD FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()