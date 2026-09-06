import xarray as xr
import numpy as np
from pathlib import Path


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "processed" / "sea_ice_20220101_clean.nc"


# ---------------------------------------------------------
# Load dataset
# ---------------------------------------------------------
ds = xr.open_dataset(INPUT_FILE)

sic = ds["sea_ice_concentration"].isel(time=0)

x = ds["x"].values
y = ds["y"].values


# ---------------------------------------------------------
# Basic grid information
# ---------------------------------------------------------
print("=== GRID INFORMATION ===")

print(f"Number of X cells: {len(x)}")
print(f"Number of Y cells: {len(y)}")

print(f"X range: {x.min():.2f} -> {x.max():.2f} m")
print(f"Y range: {y.min():.2f} -> {y.max():.2f} m")

if len(x) > 1:
    print(f"X spacing: {abs(x[1] - x[0]):.2f} m")

if len(y) > 1:
    print(f"Y spacing: {abs(y[1] - y[0]):.2f} m")


# ---------------------------------------------------------
# Valid SIC coverage
# ---------------------------------------------------------
valid_mask = np.isfinite(sic.values)

valid_cells = int(valid_mask.sum())
total_cells = int(valid_mask.size)
valid_percent = valid_cells / total_cells * 100

print("\n=== VALID COVERAGE ===")

print(f"Total cells: {total_cells}")
print(f"Valid cells: {valid_cells}")
print(f"Invalid/NaN cells: {total_cells - valid_cells}")
print(f"Valid coverage: {valid_percent:.2f}%")


# ---------------------------------------------------------
# SIC coverage thresholds
# ---------------------------------------------------------
print("\n=== SEA-ICE COVERAGE THRESHOLDS ===")

for threshold in [0.01, 0.15, 0.50, 0.80]:
    mask = np.isfinite(sic.values) & (sic.values >= threshold)
    count = int(mask.sum())
    percentage = count / total_cells * 100

    print(
        f"SIC >= {threshold:.2f}: "
        f"{count} cells ({percentage:.2f}%)"
    )


# ---------------------------------------------------------
# Coordinate ordering
# ---------------------------------------------------------
print("\n=== COORDINATE ORDER ===")

if x[1] > x[0]:
    print("X increases from left -> right")
else:
    print("X decreases from left -> right")

if y[1] > y[0]:
    print("Y increases from bottom -> top")
else:
    print("Y decreases from top -> bottom")


# ---------------------------------------------------------
# Save summary
# ---------------------------------------------------------
OUTPUT_FILE = BASE_DIR / "metadata" / "spatial_grid_summary.txt"

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

    f.write("NSIDC Antarctic Sea-Ice Spatial Grid Summary\n")
    f.write("============================================\n\n")

    f.write(f"X cells: {len(x)}\n")
    f.write(f"Y cells: {len(y)}\n")

    f.write(
        f"X range: {x.min():.2f} -> {x.max():.2f} m\n"
    )

    f.write(
        f"Y range: {y.min():.2f} -> {y.max():.2f} m\n"
    )

    f.write(
        f"X spacing: {abs(x[1] - x[0]):.2f} m\n"
    )

    f.write(
        f"Y spacing: {abs(y[1] - y[0]):.2f} m\n"
    )

    f.write(f"Total cells: {total_cells}\n")
    f.write(f"Valid cells: {valid_cells}\n")
    f.write(f"Valid coverage: {valid_percent:.2f}%\n")

print(f"\nSummary saved to:")
print(OUTPUT_FILE)