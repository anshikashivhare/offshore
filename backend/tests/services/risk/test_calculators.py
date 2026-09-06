import pytest
import pytest_asyncio
from datetime import datetime, timezone
from app.services.risk.calculators import (
    IceRiskCalculator,
    IcebergRiskCalculator,
    WeatherRiskCalculator,
    CurrentRiskCalculator
)

@pytest.mark.asyncio
async def test_ice_risk_calculator():
    calc = IceRiskCalculator()
    result = await calc.calculate(0.0, 0.0, datetime.now(timezone.utc))
    assert result.risk_value == 0.5
    assert result.confidence == 0.8
    assert not result.is_missing
    assert "source" in result.metadata

@pytest.mark.asyncio
async def test_iceberg_risk_calculator():
    calc = IcebergRiskCalculator()
    result = await calc.calculate(0.0, 0.0, datetime.now(timezone.utc))
    assert result.risk_value == 0.2
    assert result.confidence == 0.9
    assert not result.is_missing

@pytest.mark.asyncio
async def test_weather_risk_calculator():
    calc = WeatherRiskCalculator()
    result = await calc.calculate(0.0, 0.0, datetime.now(timezone.utc))
    assert result.risk_value == 0.3
    assert result.confidence == 0.85
    assert not result.is_missing

@pytest.mark.asyncio
async def test_current_risk_calculator():
    calc = CurrentRiskCalculator()
    result = await calc.calculate(0.0, 0.0, datetime.now(timezone.utc))
    assert result.risk_value == 0.1
    assert result.confidence == 0.9
    assert not result.is_missing
