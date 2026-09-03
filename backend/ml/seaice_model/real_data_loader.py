"""
Loads real gridded sea-ice concentration data from a NetCDF file
(the format NSIDC and Copernicus Marine Service both ship) and
converts it into the same long-format DataFrame schema that
generate_synthetic_timeseries() produces — so train.py works
unchanged regardless of which source you point it at.
"""

import sys
import xarray as xr
import pandas as pd


def load_netcdf_to_dataframe(nc_path: str, concentration_var: str = "sea_ice_concentration"):
    ds = xr.open_dataset(nc_path)

    if concentration_var not in ds.data_vars:
        available = list(ds.data_vars)
        raise ValueError(
            f"'{concentration_var}' not found in file. Available variables: {available}. "
            f"Pass the correct name via concentration_var=."
        )

    df = ds[concentration_var].to_dataframe().reset_index()
    df = df.rename(columns={concentration_var: "concentration", "time": "date"})

    unique_lats = sorted(df["lat"].unique(), reverse=True)
    unique_lons = sorted(df["lon"].unique())
    lat_to_row = {lat: i for i, lat in enumerate(unique_lats)}
    lon_to_col = {lon: i for i, lon in enumerate(unique_lons)}

    df["row"] = df["lat"].map(lat_to_row)
    df["col"] = df["lon"].map(lon_to_col)
    df["date"] = pd.to_datetime(df["date"])

    df = df.dropna(subset=["concentration"])

    return df[["row", "col", "date", "lat", "lon", "concentration"]]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m ml.seaice_model.real_data_loader path/to/file.nc")
        sys.exit(1)

    df = load_netcdf_to_dataframe(sys.argv[1])
    print(f"Loaded {len(df)} rows")
    print(df.head())
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"Grid size: {df['row'].nunique()} rows x {df['col'].nunique()} cols")
