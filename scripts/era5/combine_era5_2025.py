import xarray as xr
from pathlib import Path

BASE = Path("raw/era5/2025/extracted")
OUTPUT = Path("processed/era5/era5_2025.nc")

quarters = ["Q1", "Q2", "Q3", "Q4"]

datasets = []

for quarter in quarters:
    print(f"Opening {quarter}...")

    folder = BASE / quarter

    u10_file = next(folder.glob("10m_u_component_of_wind*.nc"))
    v10_file = next(folder.glob("10m_v_component_of_wind*.nc"))
    t2m_file = next(folder.glob("2m_temperature*.nc"))
    sp_file = next(folder.glob("surface_pressure*.nc"))

    u10 = xr.open_dataset(u10_file)["u10"]
    v10 = xr.open_dataset(v10_file)["v10"]
    t2m = xr.open_dataset(t2m_file)["t2m"]
    sp = xr.open_dataset(sp_file)["sp"]

    ds = xr.Dataset(
        {
            "t2m": t2m,
            "u10": u10,
            "v10": v10,
            "sp": sp,
        }
    )

    datasets.append(ds)

    print(f"  {quarter}: loaded")

print("\nConcatenating quarters...")

combined = xr.concat(
    datasets,
    dim="valid_time"
)

combined = combined.sortby("valid_time")

combined = combined.rename(
    {"valid_time": "time"}
)

combined["t2m"].attrs["long_name"] = "2 metre air temperature"
combined["u10"].attrs["long_name"] = "10 metre eastward wind component"
combined["v10"].attrs["long_name"] = "10 metre northward wind component"
combined["sp"].attrs["long_name"] = "Surface pressure"

combined.attrs["source"] = "ERA5 reanalysis"
combined.attrs["processing"] = "2025 quarterly daily-mean files combined"
combined.attrs["spatial_region"] = "50S to 90S, all longitudes"

print("\nSaving...")

combined.to_netcdf(
    OUTPUT,
    engine="netcdf4"
)

print(f"\nSaved: {OUTPUT}")
print("\nFinal dataset:")
print(combined)

print("\nTime coverage:")
print(f"First: {combined.time.values[0]}")
print(f"Last:  {combined.time.values[-1]}")
print(f"Days:  {combined.sizes['time']}")

for var in ["t2m", "u10", "v10", "sp"]:
    print(f"{var}: {combined[var].dims}")

for ds in datasets:
    ds.close()

print("\nCombination complete.")