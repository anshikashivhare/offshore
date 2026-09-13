from datetime import datetime
from typing import Any, Optional

from app.ingestion.interfaces import (DataFetcher, DataNormalizer, DataSource,
                                      DataValidator, SpatialAligner,
                                      TemporalAligner)


class OceanDataSource(DataSource):
    name = "Copernicus Marine Service"
    description = "Global Ocean Physics Analysis and Forecast"
    homepage = "https://marine.copernicus.eu/"


class CMEMSFetcher(DataFetcher):
    async def fetch(self, **kwargs) -> Any:
        return {"type": "mock_cmems", "data": "raw_netcdf"}


class CMEMSValidator(DataValidator):
    def validate(self, raw_data: Any) -> bool:
        return True


class CMEMSNormalizer(DataNormalizer):
    def normalize(self, raw_data: Any) -> Any:
        return {"type": "normalized_ocean"}


class OceanSpatialAligner(SpatialAligner):
    def align_spatial(self, normalized_data: Any, bbox: Optional[tuple] = None) -> Any:
        return normalized_data


class OceanTemporalAligner(TemporalAligner):
    def align_temporal(
        self,
        spatial_aligned_data: Any,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Any:
        return spatial_aligned_data
