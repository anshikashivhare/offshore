import xarray as xr
import matplotlib.pyplot as plt
from pathlib import Path


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "processed" / "sea_ice_20220101_clean.nc"
OUTPUT_FILE = BASE_DIR / "processed" / "sea_ice_20220101_preview.png"


# ---------------------------------------------------------
# Load cleaned dataset
# ---------------------------------------------------------
ds = xr.open_dataset(INPUT_FILE)

print("Dataset:")
print(ds)

print("\nVariables:")
print(list(ds.data_vars))

# ---------------------------------------------------------
# Extract sea-ice concentration
# ---------------------------------------------------------
sic = ds["sea_ice_concentration"].isel(time=0)

print("\nSea-ice concentration:")
print(sic)

print("\nShape:", sic.shape)
print("Min:", float(sic.min(skipna=True)))
print("Max:", float(sic.max(skipna=True)))
print("Mean:", float(sic.mean(skipna=True)))


# ---------------------------------------------------------
# Plot
# ---------------------------------------------------------
plt.figure(figsize=(10, 8))

sic.plot(
    x="x",
    y="y",
    cmap="Blues",
    vmin=0,
    vmax=1,
    cbar_kwargs={
        "label": "Sea Ice Concentration"
    }
)

plt.title("Antarctic Sea-Ice Concentration\n2022-01-01")
plt.xlabel("X coordinate (m)")
plt.ylabel("Y coordinate (m)")

plt.tight_layout()

# ---------------------------------------------------------
# Save preview
# ---------------------------------------------------------
plt.savefig(
    OUTPUT_FILE,
    dpi=200,
    bbox_inches="tight"
)

plt.close()

print(f"\nPreview saved to:")
print(OUTPUT_FILE)