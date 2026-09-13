"""
Loads real iceberg trajectory data and merges it with reanalysis
ocean current / wind data, producing the same schema
generate_synthetic_tracks() does — so train.py works unchanged.
"""

import sys

import pandas as pd
import xarray as xr


def load_track_csv(csv_path: str) -> pd.DataFrame:
    """Expects columns: iceberg_id, date, lat, lon."""
    df = pd.read_csv(csv_path, parse_dates=["date"])
    required = {"iceberg_id", "date", "lat", "lon"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Track CSV is missing columns: {missing}")
    return df.sort_values(["iceberg_id", "date"])


def nearest_env_value(ds: xr.Dataset, var: str, date, lat: float, lon: float) -> float:
    return float(ds[var].sel(time=date, lat=lat, lon=lon, method="nearest").values)


def merge_tracks_with_environment(
    tracks: pd.DataFrame,
    reanalysis_nc_path: str,
    current_u_var: str = "uo",
    current_v_var: str = "vo",
    wind_u_var: str = "u10",
    wind_v_var: str = "v10",
) -> pd.DataFrame:
    """
    For each track point, looks up the nearest reanalysis current/wind
    values, and computes next_delta_lat/next_delta_lon from the next
    observation of the same iceberg. Each iceberg's last point is
    dropped (no "next" position to compute a delta from).
    """
    ds = xr.open_dataset(reanalysis_nc_path)
    rows = []

    for iceberg_id, group in tracks.groupby("iceberg_id"):
        group = group.sort_values("date").reset_index(drop=True)
        for i in range(len(group) - 1):
            row = group.iloc[i]
            next_row = group.iloc[i + 1]

            current_u = nearest_env_value(
                ds, current_u_var, row["date"], row["lat"], row["lon"]
            )
            current_v = nearest_env_value(
                ds, current_v_var, row["date"], row["lat"], row["lon"]
            )
            wind_u = nearest_env_value(
                ds, wind_u_var, row["date"], row["lat"], row["lon"]
            )
            wind_v = nearest_env_value(
                ds, wind_v_var, row["date"], row["lat"], row["lon"]
            )

            rows.append(
                {
                    "iceberg_id": iceberg_id,
                    "timestep": i,
                    "lat": row["lat"],
                    "lon": row["lon"],
                    "current_u": current_u,
                    "current_v": current_v,
                    "wind_u": wind_u,
                    "wind_v": wind_v,
                    "next_delta_lat": next_row["lat"] - row["lat"],
                    "next_delta_lon": next_row["lon"] - row["lon"],
                }
            )

    return pd.DataFrame(rows)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python -m ml.preprocessing.trajectory.real_data_loader tracks.csv reanalysis.nc"
        )
        sys.exit(1)

    tracks = load_track_csv(sys.argv[1])
    print(
        f"Loaded {len(tracks)} track points across {tracks['iceberg_id'].nunique()} icebergs"
    )

    merged = merge_tracks_with_environment(tracks, sys.argv[2])
    print(f"Merged into {len(merged)} training rows")
    print(merged.head())
