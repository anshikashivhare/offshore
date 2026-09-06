import xarray as xr
from pathlib import Path


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

Q1_DIR = (
    PROJECT_ROOT
    / "raw"
    / "era5"
    / "2026"
    / "extracted"
    / "Q1"
)

Q2_DIR = (
    PROJECT_ROOT
    / "processed"
    / "era5"
    / "2026"
    / "Q2"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "processed"
    / "era5"
    / "2026"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "era5_2026.nc"


# ---------------------------------------------------------
# Load one quarter
# ---------------------------------------------------------

def load_quarter(folder: Path) -> xr.Dataset:

    print(f"\nLoading: {folder}")

    u10_file = next(folder.glob("10m_u_component_of_wind*.nc"))
    v10_file = next(folder.glob("10m_v_component_of_wind*.nc"))
    t2m_file = next(folder.glob("2m_temperature*.nc"))
    sp_file = next(folder.glob("surface_pressure*.nc"))

    u10 = xr.open_dataset(u10_file)["u10"]
    v10 = xr.open_dataset(v10_file)["v10"]
    t2m = xr.open_dataset(t2m_file)["t2m"]
    sp = xr.open_dataset(sp_file)["sp"]

    return xr.Dataset(
        {
            "t2m": t2m,
            "u10": u10,
            "v10": v10,
            "sp": sp,
        }
    )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("=" * 60)
    print("COMBINING ERA5 2026")
    print("=" * 60)

    q1 = load_quarter(Q1_DIR)
    q2 = load_quarter(Q2_DIR)

    print("\nConcatenating Q1 + Q2...")

    combined = xr.concat(
        [q1, q2],
        dim="valid_time"
    )

    combined = combined.sortby("valid_time")

    combined = combined.rename(
        {"valid_time": "time"}
    )

    combined.attrs["source"] = "ERA5 reanalysis"
    combined.attrs["processing"] = (
        "Q1 January-March + Q2 April-June 23, 2026"
    )
    combined.attrs["spatial_region"] = (
        "50S to 90S, all longitudes"
    )

    print("\nSaving:")
    print(OUTPUT_FILE)

    combined.to_netcdf(
        OUTPUT_FILE,
        engine="netcdf4"
    )

    print("\n=== FINAL DATASET ===")
    print(combined)

    print("\n=== TIME ===")

    print(
        f"First: {str(combined.time.values[0])[:10]}"
    )

    print(
        f"Last:  {str(combined.time.values[-1])[:10]}"
    )

    print(
        f"Days:  {combined.sizes['time']}"
    )

    print("\nSaved successfully.")

    q1.close()
    q2.close()


if __name__ == "__main__":
    main()