import pytest
from app.ingestion.adapters.weather import (
    WeatherDataSource, ERA5Fetcher, ERA5Validator, 
    ERA5Normalizer, WeatherSpatialAligner, WeatherTemporalAligner
)

@pytest.mark.asyncio
async def test_weather_adapter_stubs():
    source = WeatherDataSource()
    assert source.name == "ERA5 Reanalysis"
    
    fetcher = ERA5Fetcher()
    data = await fetcher.fetch()
    assert data["type"] == "mock_era5"
    
    validator = ERA5Validator()
    assert validator.validate(data) is True
    
    normalizer = ERA5Normalizer()
    normalized = normalizer.normalize(data)
    assert normalized["type"] == "normalized_weather"
