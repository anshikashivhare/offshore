from datetime import datetime
from typing import Any, Optional

from app.ingestion.interfaces import (DataFetcher, DataNormalizer, DataSource,
                                      DataValidator, SpatialAligner,
                                      TemporalAligner)


class AISDataSource(DataSource):
    name = "Global AIS Network"
    description = "Automatic Identification System vessel positions"
    homepage = "https://www.exactearth.com/"


class AISFetcher(DataFetcher):
    async def fetch(self, **kwargs) -> Any:
        return {"type": "mock_ais", "data": "raw_json"}


class AISValidator(DataValidator):
    def validate(self, raw_data: Any) -> bool:
        return True


class AISNormalizer(DataNormalizer):
    def normalize(self, raw_data: Any) -> Any:
        return {"type": "normalized_vessel_positions"}


class AISSpatialAligner(SpatialAligner):
    def align_spatial(self, normalized_data: Any, bbox: Optional[tuple] = None) -> Any:
        return normalized_data


class AISTemporalAligner(TemporalAligner):
    def align_temporal(
        self,
        spatial_aligned_data: Any,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Any:
        return spatial_aligned_data
