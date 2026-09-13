from datetime import datetime
from typing import Any, Optional

from app.ingestion.interfaces import (DataFetcher, DataNormalizer, DataSource,
                                      DataValidator, SpatialAligner,
                                      TemporalAligner)


class IcebergDataSource(DataSource):
    name = "Sentinel-1 Iceberg Tracking"
    description = "SAR imagery derived iceberg detections"
    homepage = "https://sentinels.copernicus.eu/"


class SentinelFetcher(DataFetcher):
    async def fetch(self, **kwargs) -> Any:
        return {"type": "mock_sentinel", "data": "raw_geojson"}


class SentinelValidator(DataValidator):
    def validate(self, raw_data: Any) -> bool:
        return True


class SentinelNormalizer(DataNormalizer):
    def normalize(self, raw_data: Any) -> Any:
        return {"type": "normalized_iceberg_detections"}


class IcebergSpatialAligner(SpatialAligner):
    def align_spatial(self, normalized_data: Any, bbox: Optional[tuple] = None) -> Any:
        return normalized_data


class IcebergTemporalAligner(TemporalAligner):
    def align_temporal(
        self,
        spatial_aligned_data: Any,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Any:
        return spatial_aligned_data
