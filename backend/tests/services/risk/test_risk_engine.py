import pytest
from datetime import datetime, timezone
from app.services.risk.engine import RiskEngine
from app.services.risk.calculators import RiskCalculator, RiskComponentResult
from app.models.enums import RiskCategory

class MockCalculator(RiskCalculator):
    def __init__(self, risk_value: float, is_missing: bool = False):
        self.risk_value = risk_value
        self.is_missing = is_missing
        
    async def calculate(self, lat: float, lon: float, timestamp: datetime) -> RiskComponentResult:
        return RiskComponentResult(
            risk_value=self.risk_value,
            confidence=1.0,
            is_missing=self.is_missing,
            metadata={}
        )

@pytest.mark.asyncio
async def test_risk_engine_weighted_aggregation():
    engine = RiskEngine(
        ice_calc=MockCalculator(1.0),
        iceberg_calc=MockCalculator(0.5),
        weather_calc=MockCalculator(0.0),
        current_calc=MockCalculator(0.0)
    )
    
    weights = {"ice": 0.5, "iceberg": 0.5, "weather": 0.0, "current": 0.0}
    cell = await engine.calculate_cell_risk(0.0, 0.0, datetime.now(timezone.utc), "POINT(0 0)", weights=weights)
    
    # 1.0*0.5 + 0.5*0.5 = 0.75
    assert cell.composite_risk == 0.75
    assert cell.risk_category == RiskCategory.AVOID
    assert cell.missing_data_flags["ice"] is False

@pytest.mark.asyncio
async def test_risk_engine_missing_data():
    engine = RiskEngine(
        ice_calc=MockCalculator(1.0, is_missing=True),
        iceberg_calc=MockCalculator(0.5),
        weather_calc=MockCalculator(0.0),
        current_calc=MockCalculator(0.0)
    )
    
    # Ice is missing. Weights: 0.5 iceberg, 0.5 ice (missing) -> normalizes to 0.5 weight for iceberg.
    # composite_risk = 0.5 * 0.5 / 0.5 = 0.5
    weights = {"ice": 0.5, "iceberg": 0.5, "weather": 0.0, "current": 0.0}
    cell = await engine.calculate_cell_risk(0.0, 0.0, datetime.now(timezone.utc), "POINT(0 0)", weights=weights)
    
    assert cell.composite_risk == 0.5
    assert cell.risk_category == RiskCategory.HIGH
    assert cell.missing_data_flags["ice"] is True

def test_risk_engine_weight_validation():
    engine = RiskEngine()
    with pytest.raises(ValueError, match="Sum of weights must be greater than zero"):
        engine._validate_weights({"ice": 0.0, "iceberg": 0.0})

    with pytest.raises(ValueError, match="Weight for ice cannot be negative"):
        engine._validate_weights({"ice": -0.1, "iceberg": 0.5})

@pytest.mark.asyncio
async def test_extreme_hazard_conditions():
    engine = RiskEngine(
        ice_calc=MockCalculator(1.0),
        iceberg_calc=MockCalculator(1.0),
        weather_calc=MockCalculator(1.0),
        current_calc=MockCalculator(1.0)
    )
    
    cell = await engine.calculate_cell_risk(0.0, 0.0, datetime.now(timezone.utc), "POINT(0 0)")
    assert cell.composite_risk == 1.0
    assert cell.risk_category == RiskCategory.AVOID

@pytest.mark.asyncio
async def test_thresholds():
    engine = RiskEngine()
    assert engine._categorize_risk(0.1) == RiskCategory.LOW
    assert engine._categorize_risk(0.3) == RiskCategory.MODERATE
    assert engine._categorize_risk(0.6) == RiskCategory.HIGH
    assert engine._categorize_risk(0.8) == RiskCategory.AVOID
