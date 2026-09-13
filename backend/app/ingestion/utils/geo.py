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
    """
    if gdf.crs is None:
        gdf.set_crs(epsg=target_epsg, inplace=True)
    elif gdf.crs.to_epsg() != target_epsg:
        gdf.to_crs(epsg=target_epsg, inplace=True)
    return gdf
