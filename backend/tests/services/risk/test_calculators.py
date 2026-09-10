import pytest
import pytest_asyncio
from datetime import datetime, timezone
from app.services.risk.calculators import (
    IceRiskCalculator,
    IcebergRiskCalculator,
    WeatherRiskCalculator,
    CurrentRiskCalculator
)

class MockDB:
    async def execute(self, stmt):
        class Result:
            def scalars(self):
                class Scalars:
                    def all(self): return []
                return Scalars()
        return Result()

@pytest.mark.asyncio
async def test_ice_risk_calculator():
    calc = IceRiskCalculator(db=MockDB())
    result = await calc.calculate(0.0, 0.0, datetime.now(timezone.utc))
    assert result.risk_value == 0.0
    assert result.is_missing

@pytest.mark.asyncio
async def test_iceberg_risk_calculator():
    calc = IcebergRiskCalculator(db=MockDB())
    result = await calc.calculate(0.0, 0.0, datetime.now(timezone.utc))
    assert result.risk_value == 0.0
    assert result.is_missing

@pytest.mark.asyncio
async def test_weather_risk_calculator():
    calc = WeatherRiskCalculator(db=MockDB())
    result = await calc.calculate(0.0, 0.0, datetime.now(timezone.utc))
    assert result.risk_value == 0.0
    assert result.is_missing

@pytest.mark.asyncio
async def test_current_risk_calculator():
    calc = CurrentRiskCalculator(db=MockDB())
    result = await calc.calculate(0.0, 0.0, datetime.now(timezone.utc))
    assert result.risk_value == 0.0
    assert result.is_missing
