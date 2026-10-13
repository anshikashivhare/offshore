import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.models.enums import ObjectiveType
from app.models.vessel import Vessel
from app.schemas.route import RouteCreate, RouteRequest, WaypointDetail
from app.services.routing.comparison import RouteComparisonService
from app.services.routing.validator import route_validator


class EnvironmentalPlanner:
    def __init__(self, samples):
        self.samples = samples

    async def plan_route(self, request, vessel, risk_grid, demo_mode=False):
        return RouteCreate(
            vessel_id=request.vessel_id,
            origin=request.origin,
            destination=request.destination,
            departure_time=request.departure_time,
            distance=4500.0,
            travel_time=450.0,
            eta=request.departure_time + timedelta(hours=450),
            estimated_fuel=1000.0,
            risk_score=0.2,
            risk_exposure=900.0,
            objective_type=request.objective_type,
            geometry="LINESTRING(166.67 -77.84, 115.74 -32.05)",
            waypoints=[
                WaypointDetail(
                    lat=-77.84,
                    lon=166.67,
                    eta=request.departure_time,
                    data_provenance="test",
                    env_conditions=sample,
                )
                for sample in self.samples
            ],
        )


async def compare_samples(samples, monkeypatch):
    # These tests isolate comparison from pathfinding and land-mask datasets.
    monkeypatch.setattr(
        route_validator, "validate_wkt_linestring", lambda *args, **kwargs: (True, None, None)
    )
    vessel = Vessel(
        vessel_id=uuid.UUID("123e4567-e89b-12d3-a456-426614174001"),
        vessel_name="Test",
        cruising_speed=10.0,
        fuel_consumption=10.0,
    )
    request = RouteRequest(
        origin="166.67,-77.84",
        destination="115.74,-32.05",
        vessel_id=vessel.vessel_id,
        departure_time=datetime(2026, 10, 9, tzinfo=timezone.utc),
        objective_type=ObjectiveType.SAFEST,
    )
    return await RouteComparisonService(EnvironmentalPlanner(samples)).compare_routes(
        request, vessel, {}
    )


@pytest.mark.asyncio
async def test_safety_first_comparison_with_nullable_environmental_values(monkeypatch):
    response = await compare_samples(
        [
            {"wave_height": None, "sea_ice_concentration": None},
            {"wave_height": 0, "sea_ice_concentration": 0},
            {"wave_height": 4, "sea_ice_concentration": 0.6},
            {},
        ],
        monkeypatch,
    )

    assert response.recommended_route.properties.objective_type == ObjectiveType.SAFEST
    assert len(response.alternatives) == 3
    assert response.risk_factors == {
        "average_wave_height": 2.0,
        "average_sea_ice_concentration": 0.3,
    }
    assert response.recommended_route.properties.waypoints[0].env_conditions == {
        "wave_height": None,
        "sea_ice_concentration": None,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid",
    [None, "bad", "2.5", True, False, float("nan"), float("inf"), -float("inf"), {}, []],
    ids=[
        "null", "text", "numeric-text", "true", "false",
        "nan", "inf", "negative-inf", "object", "array",
    ],
)
async def test_only_finite_numeric_samples_contribute_to_averages(invalid, monkeypatch):
    response = await compare_samples(
        [
            {"wave_height": invalid, "sea_ice_concentration": invalid},
            {"wave_height": 2.0, "sea_ice_concentration": 0.4},
            {"wave_height": 4, "sea_ice_concentration": 0.8},
        ],
        monkeypatch,
    )

    assert response.risk_factors["average_wave_height"] == 3.0
    assert response.risk_factors["average_sea_ice_concentration"] == pytest.approx(0.6)


@pytest.mark.asyncio
async def test_environmental_fields_have_independent_missing_sample_counts(monkeypatch):
    response = await compare_samples(
        [
            {"wave_height": None, "sea_ice_concentration": 0.4},
            {"wave_height": 4.0},
        ],
        monkeypatch,
    )

    assert response.risk_factors == {
        "average_wave_height": 4.0,
        "average_sea_ice_concentration": 0.4,
    }


@pytest.mark.asyncio
async def test_no_valid_environmental_samples_leaves_averages_missing(monkeypatch):
    response = await compare_samples(
        [
            {},
            {"wave_height": None, "sea_ice_concentration": None},
            {"wave_height": float("nan"), "sea_ice_concentration": True},
            {"wave_height": "0", "sea_ice_concentration": float("inf")},
        ],
        monkeypatch,
    )

    assert response.risk_factors == {}


@pytest.mark.asyncio
async def test_observed_zero_is_included_in_environmental_averages(monkeypatch):
    response = await compare_samples(
        [{"wave_height": 0, "sea_ice_concentration": 0.0}], monkeypatch
    )

    assert response.risk_factors == {
        "average_wave_height": 0.0,
        "average_sea_ice_concentration": 0.0,
    }
