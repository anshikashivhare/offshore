import pytest
from app.ingestion.pipeline import IngestionPipeline
from app.ingestion.adapters.sea_ice import (
    SeaIceDataSource, NSIDCFetcher, NSIDCValidator, 
    NSIDCNormalizer, SeaIceSpatialAligner, SeaIceTemporalAligner
)

@pytest.mark.asyncio
async def test_sea_ice_pipeline_execution():
    pipeline = IngestionPipeline(
        source=SeaIceDataSource(),
        fetcher=NSIDCFetcher(),
        validator=NSIDCValidator(),
        normalizer=NSIDCNormalizer(),
        spatial_aligner=SeaIceSpatialAligner(),
        temporal_aligner=SeaIceTemporalAligner(),
    )
    
    result = await pipeline.run()
    
    assert result is not None
    assert result.get("type") == "normalized"
    assert result.get("concentration") == 0.8

@pytest.mark.asyncio
async def test_sea_ice_pipeline_validation_failure():
    class FailingValidator(NSIDCValidator):
        def validate(self, raw_data):
            raise ValueError("Invalid data structure")

    pipeline = IngestionPipeline(
        source=SeaIceDataSource(),
        fetcher=NSIDCFetcher(),
        validator=FailingValidator(),
        normalizer=NSIDCNormalizer(),
        spatial_aligner=SeaIceSpatialAligner(),
        temporal_aligner=SeaIceTemporalAligner(),
    )
    
    with pytest.raises(ValueError, match="Invalid data structure"):
        await pipeline.run()
