import logging
import uuid
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import RiskCategory
from app.schemas.risk import RiskCellCreate
from app.services.risk.calculators import (
    CurrentRiskCalculator,
    IceRiskCalculator,
    IcebergRiskCalculator,
    RiskCalculator,
    WeatherRiskCalculator,
)

logger = logging.getLogger(__name__)


DEFAULT_WEIGHTS: Dict[str, float] = {
    "ice": 0.25,
    "iceberg": 0.25,
    "weather": 0.25,
    "current": 0.25,
}


class RiskAggregationStrategy(ABC):
    @abstractmethod
    def aggregate(
        self, results: Dict[str, "object"], weights: Dict[str, float]
    ) -> float: ...


class WeightedSumStrategy(RiskAggregationStrategy):
    def aggregate(
        self, results: Dict[str, "object"], weights: Dict[str, float]
    ) -> float:
        total_risk = 0.0
        total_weight = 0.0
        for key, weight in weights.items():
            if key in results and not results[key].is_missing:
                total_risk += results[key].risk_value * weight
                total_weight += weight
        if total_weight > 0:
            return total_risk / total_weight
        return 0.0


class RiskEngine:
    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        *,
        ice_calc: Optional[RiskCalculator] = None,
        iceberg_calc: Optional[RiskCalculator] = None,
        weather_calc: Optional[RiskCalculator] = None,
        current_calc: Optional[RiskCalculator] = None,
        aggregation_strategy: Optional[RiskAggregationStrategy] = None,
    ):
        if db is not None and ice_calc is None:
            ice_calc = IceRiskCalculator(db)
        if db is not None and iceberg_calc is None:
            iceberg_calc = IcebergRiskCalculator(db)
        if db is not None and weather_calc is None:
            weather_calc = WeatherRiskCalculator(db)
        if db is not None and current_calc is None:
            current_calc = CurrentRiskCalculator(db)
        self.calculators = {
            "ice": ice_calc or IceRiskCalculator(db) if db else (ice_calc or _StubIce()),
            "iceberg": iceberg_calc
            or IcebergRiskCalculator(db)
            if db
            else (iceberg_calc or _StubIceberg()),
            "weather": weather_calc
            or WeatherRiskCalculator(db)
            if db
            else (weather_calc or _StubWeather()),
            "current": current_calc
            or CurrentRiskCalculator(db)
            if db
            else (current_calc or _StubCurrent()),
        }
        self.aggregation_strategy = aggregation_strategy or WeightedSumStrategy()

    def _validate_weights(self, weights: Dict[str, float]) -> None:
        if not weights:
            raise ValueError("Weights cannot be empty")
        total = sum(weights.values())
        if total <= 0:
            raise ValueError("Sum of weights must be greater than zero")
        for key, weight in weights.items():
            if weight < 0:
                raise ValueError(f"Weight for {key} cannot be negative")

    def _categorize_risk(self, composite_risk: float) -> RiskCategory:
        if composite_risk < 0.25:
            return RiskCategory.LOW
        if composite_risk < 0.5:
            return RiskCategory.MODERATE
        if composite_risk < 0.75:
            return RiskCategory.HIGH
        return RiskCategory.AVOID

    async def calculate_cell_risk(
        self,
        lat: float,
        lon: float,
        timestamp: datetime,
        geometry: str,
        weights: Optional[Dict[str, float]] = None,
    ) -> RiskCellCreate:
        if weights is None:
            weights = dict(DEFAULT_WEIGHTS)
        self._validate_weights(weights)

        results: Dict[str, "object"] = {}
        missing_data_flags: Dict[str, bool] = {}
        metadata_info: Dict[str, dict] = {}
        overall_confidence = 1.0
        for key, calc in self.calculators.items():
            result = await calc.calculate(lat, lon, timestamp)
            results[key] = result
            missing_data_flags[key] = result.is_missing
            metadata_info[f"{key}_metadata"] = result.metadata
            overall_confidence *= result.confidence

        composite_risk = self.aggregation_strategy.aggregate(results, weights)
        category = self._categorize_risk(composite_risk)

        return RiskCellCreate(
            geometry=geometry,
            timestamp=timestamp,
            ice_risk=results["ice"].risk_value,
            iceberg_risk=results["iceberg"].risk_value,
            weather_risk=results["weather"].risk_value,
            current_risk=results["current"].risk_value,
            composite_risk=composite_risk,
            risk_category=category,
            confidence_score=overall_confidence,
            missing_data_flags=missing_data_flags,
            metadata_info=metadata_info,
        )

    async def calculate_grid_risk(
        self,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float,
        *,
        resolution_deg: float = 1.0,
        timestamp: Optional[datetime] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> List[RiskCellCreate]:
        """Compute a regular grid of risk cells across a bbox.

        The grid is sampled every ``resolution_deg`` degrees. Cells are returned
        as ``RiskCellCreate`` with the cell polygon in WKT. Missing data on all
        four components is acceptable; the resulting cell will have
        ``composite_risk=0`` and the appropriate missing flags.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        if resolution_deg <= 0:
            raise ValueError("resolution_deg must be > 0")
        if min_lat >= max_lat or min_lon >= max_lon:
            raise ValueError("Invalid bounding box: min must be < max on both axes.")

        cells: List[RiskCellCreate] = []
        lat = min_lat
        while lat < max_lat:
            lon = min_lon
            next_lat = min(lat + resolution_deg, max_lat)
            while lon < max_lon:
                next_lon = min(lon + resolution_deg, max_lon)
                cell_lat = (lat + next_lat) / 2.0
                cell_lon = (lon + next_lon) / 2.0
                wkt = (
                    f"POLYGON(({lon} {lat}, {next_lon} {lat}, {next_lon} {next_lat}, "
                    f"{lon} {next_lat}, {lon} {lat}))"
                )
                try:
                    cell = await self.calculate_cell_risk(
                        lat=cell_lat,
                        lon=cell_lon,
                        timestamp=timestamp,
                        geometry=wkt,
                        weights=weights,
                    )
                except Exception as exc:
                    logger.warning(
                        "Risk calc failed for cell (lat=%.3f, lon=%.3f): %s",
                        cell_lat,
                        cell_lon,
                        exc,
                    )
                    continue
                cells.append(cell)
                lon = next_lon
            lat = next_lat
        return cells


class _StubBase:
    async def calculate(self, lat, lon, timestamp):
        from app.services.risk.calculators import RiskComponentResult

        return RiskComponentResult(
            risk_value=0.5, confidence=0.5, is_missing=True,
            metadata={"source": "stub_no_db"},
        )


class _StubIce(_StubBase):
    pass


class _StubIceberg(_StubBase):
    pass


class _StubWeather(_StubBase):
    pass


class _StubCurrent(_StubBase):
    pass