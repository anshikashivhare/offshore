"""
Streaming-aware helpers for working with xarray raster datasets.

These functions deliberately avoid materialising huge rasters into memory by
relying on lazy / chunked loading via xarray + dask.
"""

from __future__ import annotations

import logging
from typing import Iterator, Optional, Tuple

import xarray as xr

logger = logging.getLogger(__name__)


def open_dataset_chunked(
    path: str,
    chunks: Optional[dict] = None,
    **open_kwargs,
) -> xr.Dataset:
    """
    Open an xarray Dataset with explicit dask chunking. The returned object
    uses lazy evaluation; values are only loaded into memory when explicitly
    requested via ``.load()`` or iteration.
    """
    chunks = chunks or {"time": 1, "lat": 256, "lon": 256}
    try:
        ds = xr.open_dataset(path, chunks=chunks, **open_kwargs)
    except Exception as exc:
        logger.error("Failed to open raster dataset %s: %s", path, exc)
        raise
    return ds


def subset_dataset_spatial(
    ds: xr.Dataset,
    bbox: Optional[Tuple[float, float, float, float]],
    lat_dim: str = "lat",
    lon_dim: str = "lon",
) -> xr.Dataset:
    """
    Subsets an xarray Dataset to a specific bounding box.
    bbox: (min_lon, min_lat, max_lon, max_lat)
    """
    if not bbox:
        return ds

    min_lon, min_lat, max_lon, max_lat = bbox
    if ds[lat_dim][0] < ds[lat_dim][-1]:
        lat_slice = slice(min_lat, max_lat)
    else:
        lat_slice = slice(max_lat, min_lat)

    sliced_ds = ds.sel(
        {
            lat_dim: lat_slice,
            lon_dim: slice(min_lon, max_lon),
        }
    )
    return sliced_ds


def subset_dataset_temporal(
    ds: xr.Dataset,
    start_time: Optional[str],
    end_time: Optional[str],
    time_dim: str = "time",
) -> xr.Dataset:
    if start_time and end_time:
        return ds.sel({time_dim: slice(start_time, end_time)})
    if start_time:
        return ds.sel({time_dim: slice(start_time, None)})
    if end_time:
        return ds.sel({time_dim: slice(None, end_time)})
    return ds


def iter_chunks(
    ds: xr.Dataset,
    lat_dim: str = "lat",
    lon_dim: str = "lon",
    chunk_rows: int = 64,
) -> Iterator[xr.Dataset]:
    """
    Iterate over the spatial extent of ``ds`` in fixed-row chunks.

    This is the canonical way to iterate over a large raster without ever
    loading it into memory. Each yielded chunk is itself a lazy xarray
    Dataset; downstream code can decide whether to materialise it.
    """
    if lat_dim not in ds.dims:
        raise ValueError(f"Latitude dimension '{lat_dim}' not in dataset.")
    n_lat = ds.sizes[lat_dim]
    for start in range(0, n_lat, chunk_rows):
        end = min(start + chunk_rows, n_lat)
        yield ds.isel({lat_dim: slice(start, end)})


__all__ = [
    "open_dataset_chunked",
    "subset_dataset_spatial",
    "subset_dataset_temporal",
    "iter_chunks",
]
