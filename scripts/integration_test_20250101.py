from pathlib import Path
import xarray as xr
import numpy as np

PROJECT = Path(r"C:\PROJECTS\DATA-OFFSHORE")

NSIDC = PROJECT / "processed" / "nsidc" / "2025"
ERA5 = PROJECT / "processed" / "era5" / "era5_2025.nc"
MARINE = PROJECT / "raw" / "copernicus_marine" / "2025" / "copernicus_marine_2025.nc"


def find_nsidc_file():
    files = sorted(NSIDC.glob("*.nc"))
    for f in files:
        if "20250101" in f.name:
            return f
    raise FileNotFoundError("2025-01-01 NSIDC processed file not found.")


print("=" * 70)
print("1-DAY INTEGRATION TEST — 2025-01-01")
print("=" * 70)

# ---------------------------------------------------------
# NSIDC
# ---------------------------------------------------------

sic_file = find_nsidc_file()

with xr.open_dataset(sic_file) as ds_sic:
    sic = ds_sic["sea_ice_concentration"]

    print("\nNSIDC")
    print("  shape:", sic.shape)
    print("  dims :", sic.dims)
    print("  x/y  :", len(ds_sic.x), len(ds_sic.y))

    sic_latlon_note = "Native EPSG:3412 grid retained."

# ---------------------------------------------------------
# ERA5
# ---------------------------------------------------------

with xr.open_dataset(ERA5) as ds_era5:

    era5 = ds_era5.sel(
        time="2025-01-01"
    )

    print("\nERA5")
    print("  t2m shape:", era5["t2m"].shape)
    print("  latitude :", float(era5.latitude.min()), "to", float(era5.latitude.max()))
    print("  longitude:", float(era5.longitude.min()), "to", float(era5.longitude.max()))

# ---------------------------------------------------------
# Marine
# ---------------------------------------------------------

with xr.open_dataset(
    MARINE,
    chunks={}
) as ds_marine:

    marine = ds_marine.sel(
        time="2025-01-01"
    )

    print("\nCOPERNICUS MARINE")
    print("  uo shape:", marine["uo"].shape)
    print("  vo shape:", marine["vo"].shape)
    print("  thetao shape:", marine["thetao"].shape)
    print("  latitude :", float(marine.latitude.min()), "to", float(marine.latitude.max()))
    print("  longitude:", float(marine.longitude.min()), "to", float(marine.longitude.max()))

    # Remove the single depth dimension
    marine = marine.isel(depth=0)

    print("  surface uo shape:", marine["uo"].shape)

# ---------------------------------------------------------
# Basic overlap checks
# ---------------------------------------------------------

print("\nOVERLAP")
print("  Time: 2025-01-01 ✓")

print(
    "  Latitude overlap:",
    max(float(era5.latitude.min()), float(marine.latitude.min())),
    "to",
    min(float(era5.latitude.max()), float(marine.latitude.max())),
)

print(
    "  Longitude overlap:",
    max(float(era5.longitude.min()), float(marine.longitude.min())),
    "to",
    min(float(era5.longitude.max()), float(marine.longitude.max())),
)

print("\nNSIDC:")
print(" ", sic_latlon_note)

print("\nTEST COMPLETE")