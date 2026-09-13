from datetime import datetime
from typing import Any, Optional

from app.ingestion.interfaces import (DataFetcher, DataNormalizer, DataSource,
                                      DataValidator, SpatialAligner,
                                      TemporalAligner)


class WeatherDataSource(DataSource):
    name = "ERA5 Reanalysis"
    description = "ECMWF ERA5 hourly data on single levels"
    homepage = "https://cds.climate.copernicus.eu/"


class ERA5Fetcher(DataFetcher):
    async def fetch(self, **kwargs) -> Any:
        return {"type": "mock_era5", "data": "raw_grib"}


class ERA5Validator(DataValidator):
    def validate(self, raw_data: Any) -> bool:
        return True


class ERA5Normalizer(DataNormalizer):
    def normalize(self, raw_data: Any) -> Any:
        return {"type": "normalized_weather"}


class WeatherSpatialAligner(SpatialAligner):
    def align_spatial(self, normalized_data: Any, bbox: Optional[tuple] = None) -> Any:
        return normalized_data


class WeatherTemporalAligner(TemporalAligner):
    def align_temporal(
        self,
        spatial_aligned_data: Any,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Any:
        return spatial_aligned_data
