from typing import Optional

import geopandas as gpd
from shapely.geometry import box


def clip_to_bbox_vector(
    gdf: gpd.GeoDataFrame, bbox: Optional[tuple]
) -> gpd.GeoDataFrame:
    """
    Clips a GeoDataFrame to a given bounding box.
    bbox: (min_lon, min_lat, max_lon, max_lat)
    """
    if not bbox:
        return gdf

    bounding_box = box(*bbox)
    # Clip the data safely
    clipped = gpd.clip(gdf, bounding_box)
    return clipped


def normalize_crs(gdf: gpd.GeoDataFrame, target_epsg: int = 4326) -> gpd.GeoDataFrame:
    """
    Ensures the GeoDataFrame uses the target EPSG.

    A missing CRS is a data-quality failure, not evidence that the coordinates
    are WGS84.  Silently assigning EPSG:4326 would place projected polar data
    in the wrong location while appearing plausible on a map.
    """
    if gdf.crs is None:
        raise ValueError(
            "Input vector data has no CRS. Declare its source CRS before "
            f"transforming it to EPSG:{target_epsg}."
        )
    elif gdf.crs.to_epsg() != target_epsg:
        gdf.to_crs(epsg=target_epsg, inplace=True)
    return gdf
