import os
import re
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

# Optional imports – will be available in the training environment
try:
    import xarray as xr
except ImportError:  # pragma: no cover
    xr = None

try:
    import rasterio
    from rasterio.enums import Resampling
except ImportError:  # pragma: no cover
    rasterio = None


def _parse_date_from_filename(fname: str) -> pd.Timestamp:
    """Extract a date (YYYYMMDD) from a filename.

    Looks for an 8‑digit sequence and returns a pandas Timestamp.
    Raises ValueError if not found.
    """
    m = re.search(r"(\d{8})", fname)
    if not m:
        raise ValueError(f"Cannot parse date from filename '{fname}'. Expected YYYYMMDD.")
    return pd.to_datetime(m.group(1), format="%Y%m%d")


def _process_netcdf(path: Path, variable_name: str) -> List[dict]:
    """Read a NetCDF file and return a list of record dicts.

    Supports two common layouts:
    1. A "time" dimension inside the file (e.g., shape (time, lat, lon)).
    2. A single‑day grid with the date encoded in the filename.
    """
    if xr is None:
        raise ImportError("xarray is required to read NetCDF files.")
    ds = xr.open_dataset(path)
    if variable_name not in ds:
        raise KeyError(f"Variable '{variable_name}' not found in {path.name}.")
    var = ds[variable_name]
    # Normalise dimension order to (time, lat, lon) if possible
    if "time" in var.dims:
        times = var["time"].values
        lat_vals = var["lat"].values if "lat" in var.dims else None
        lon_vals = var["lon"].values if "lon" in var.dims else None
        data = var.values  # shape (time, lat, lon)
        records = []
        for t_idx, t in enumerate(times):
            date = pd.to_datetime(str(t)).floor("D")
            grid = data[t_idx]
            rows, cols = grid.shape
            for r in range(rows):
                for c in range(cols):
                    records.append({
                        "row": r,
                        "col": c,
                        "date": date,
                        "lat": float(lat_vals[r]) if lat_vals is not None else np.nan,
                        "lon": float(lon_vals[c]) if lon_vals is not None else np.nan,
                        "concentration": float(grid[r, c]),
                    })
        return records
    else:
        # No time dimension – infer date from filename
        date = _parse_date_from_filename(path.name)
        grid = var.values.squeeze()
        rows, cols = grid.shape
        lat_vals = ds["lat"].values if "lat" in ds else None
        lon_vals = ds["lon"].values if "lon" in ds else None
        records = []
        for r in range(rows):
            for c in range(cols):
                records.append({
                    "row": r,
                    "col": c,
                    "date": date,
                    "lat": float(lat_vals[r]) if lat_vals is not None else np.nan,
                    "lon": float(lon_vals[c]) if lon_vals is not None else np.nan,
                    "concentration": float(grid[r, c]),
                })
        return records


def _process_geotiff(path: Path) -> List[dict]:
    """Read a GeoTIFF file and return a list of record dicts.

    The date is parsed from the filename using the same 8‑digit rule.
    """
    if rasterio is None:
        raise ImportError("rasterio is required to read GeoTIFF files.")
    date = _parse_date_from_filename(path.name)
    with rasterio.open(path) as src:
        # Read the first band; assume single‑band concentration data
        grid = src.read(1, resampling=Resampling.nearest)
        rows, cols = grid.shape
        # Build latitude/longitude arrays from the transform
        transform = src.transform
        # Compute lat/lon for pixel centers
        xs = np.arange(cols)
        ys = np.arange(rows)
        lon_grid = transform.c + xs * transform.a + ys * transform.b
        lat_grid = transform.f + xs * transform.d + ys * transform.e
        lon_grid = lon_grid + 0.5 * transform.a
        lat_grid = lat_grid + 0.5 * transform.e
        lon_flat = lon_grid.ravel()
        lat_flat = lat_grid.ravel()
        conc_flat = grid.ravel()
        records = []
        for idx, (r, c) in enumerate(np.ndindex(rows, cols)):
            records.append({
                "row": r,
                "col": c,
                "date": date,
                "lat": float(lat_flat[idx]),
                "lon": float(lon_flat[idx]),
                "concentration": float(conc_flat[idx]),
            })
        return records


def load_real_seaice_data(data_dir: str, variable_name: str = "concentration") -> pd.DataFrame:
    """Load all NetCDF (*.nc) and GeoTIFF (*.tif) files under *data_dir*.

    Returns a long‑format DataFrame with columns:
    ``row, col, date, lat, lon, concentration``.
    """
    data_path = Path(data_dir)
    if not data_path.is_dir():
        raise NotADirectoryError(f"{data_dir} does not exist or is not a directory.")

    records = []
    for file_path in sorted(data_path.rglob("*")):
        if file_path.suffix.lower() == ".nc":
            records.extend(_process_netcdf(file_path, variable_name))
        elif file_path.suffix.lower() in {".tif", ".tiff"}:
            records.extend(_process_geotiff(file_path))
        else:
            continue

    if not records:
        raise FileNotFoundError(f"No supported sea‑ice files found in {data_dir}.")

    df = pd.DataFrame.from_records(records)
    # Ensure correct dtypes
    df["row"] = df["row"].astype(int)
    df["col"] = df["col"].astype(int)
    df["date"] = pd.to_datetime(df["date"])
    df["lat"] = df["lat"].astype(float)
    df["lon"] = df["lon"].astype(float)
    df["concentration"] = df["concentration"].astype(float)
    return df

if __name__ == "__main__":  # pragma: no cover
    import argparse
    parser = argparse.ArgumentParser(description="Load real sea‑ice data and print a summary.")
    parser.add_argument("--data-dir", type=str, required=True, help="Directory with NetCDF/GeoTIFF files.")
    parser.add_argument("--variable", type=str, default="concentration", help="Variable name inside NetCDF files.")
    args = parser.parse_args()
    df = load_real_seaice_data(args.data_dir, args.variable)
    print(f"Loaded {len(df)} rows from {df['date'].nunique()} distinct dates.")
    print(df.head())
