import json
from datetime import datetime, timezone

import httpx
import pytest

from app.services.environment.forecast_grid import ForecastGrid


TIMES = [f"2026-10-09T{hour:02d}:00" for hour in (0, 3, 6)]


async def fetch_grid(weather, marine):
    requests = []

    def respond(request):
        requests.append(request)
        if request.url.host == "api.open-meteo.com":
            hourly = weather
        else:
            assert request.url.host == "marine-api.open-meteo.com"
            hourly = marine
        # Raw JSON also lets us model malformed provider NaN/Infinity values.
        return httpx.Response(200, content=json.dumps({"hourly": hourly}))

    grid = ForecastGrid()
    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        await grid._fetch_point(client, -77.84, 166.67)
    return grid, requests


def conditions(grid, hour):
    return grid.get_conditions(
        -77.84, 166.67, datetime(2026, 10, 9, hour, tzinfo=timezone.utc)
    )


@pytest.mark.asyncio
async def test_null_and_short_arrays_preserve_valid_fields_and_zero():
    grid, _ = await fetch_grid(
        {
            "time": TIMES,
            "wind_speed_10m": [12, None, 0],
            "wind_direction_10m": [180],
        },
        {
            "time": TIMES,
            "ocean_current_velocity": [None, 0],
            "ocean_current_direction": [],
            "wave_height": [None, 2, 0],
        },
    )

    assert conditions(grid, 0) == {"wind_speed_10m": 12.0, "wind_direction_10m": 180.0}
    assert conditions(grid, 3) == {"ocean_current_velocity": 0.0, "wave_height": 2.0}
    assert conditions(grid, 6) == {"wind_speed_10m": 0.0, "wave_height": 0.0}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid",
    [None, "bad", "2.5", True, False, float("nan"), float("inf"), -float("inf"), {}, []],
    ids=[
        "null", "text", "numeric-text", "true", "false",
        "nan", "inf", "negative-inf", "object", "array",
    ],
)
async def test_invalid_sample_does_not_discard_good_fields(invalid):
    grid, _ = await fetch_grid(
        {
            "time": TIMES[:1],
            "wind_speed_10m": [invalid],
            "wind_direction_10m": [90],
        },
        {
            "time": TIMES[:1],
            "ocean_current_velocity": [invalid],
            "wave_height": [1.5],
        },
    )

    assert conditions(grid, 0) == {"wind_direction_10m": 90.0, "wave_height": 1.5}


@pytest.mark.asyncio
async def test_weather_and_marine_hours_are_aligned_by_timestamp():
    grid, _ = await fetch_grid(
        {
            "time": TIMES[:2],
            "wind_speed_10m": [10, 20],
            "wind_direction_10m": [90, 180],
        },
        {
            "time": [TIMES[2], TIMES[1]],
            "ocean_current_velocity": [0.6, 0.3],
            "ocean_current_direction": [60, 30],
            "wave_height": [6, 3],
        },
    )

    assert conditions(grid, 0) == {"wind_speed_10m": 10.0, "wind_direction_10m": 90.0}
    assert conditions(grid, 3) == {
        "wind_speed_10m": 20.0,
        "wind_direction_10m": 180.0,
        "ocean_current_velocity": 0.3,
        "ocean_current_direction": 30.0,
        "wave_height": 3.0,
    }
    assert conditions(grid, 6) == {
        "ocean_current_velocity": 0.6,
        "ocean_current_direction": 60.0,
        "wave_height": 6.0,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "malformed", [None, 7, "not-an-array", {"0": 12}],
    ids=["null", "scalar", "text", "object"],
)
async def test_malformed_series_does_not_discard_other_observations(malformed):
    grid, _ = await fetch_grid(
        {
            "time": TIMES[:1],
            "wind_speed_10m": malformed,
            "wind_direction_10m": [45],
        },
        {"time": TIMES[:1], "wave_height": [0]},
    )

    assert conditions(grid, 0) == {"wind_direction_10m": 45.0, "wave_height": 0.0}


@pytest.mark.asyncio
async def test_missing_marine_data_does_not_create_zero_or_use_weather_wave_height():
    grid, requests = await fetch_grid(
        {"time": TIMES[:1], "wind_speed_10m": [10], "wave_height": [9]},
        {},
    )

    assert conditions(grid, 0) == {"wind_speed_10m": 10.0}
    weather_request, marine_request = requests
    assert weather_request.url.params["hourly"] == "wind_speed_10m,wind_direction_10m"
    assert "wave_height" in marine_request.url.params["hourly"].split(",")


@pytest.mark.asyncio
async def test_empty_and_invalid_buckets_remain_missing():
    grid, _ = await fetch_grid(
        {
            "time": [TIMES[0], "bad-time", "2026-10-09T01:00"],
            "wind_speed_10m": [None, 3, 4],
        },
        {"time": TIMES[:1], "wave_height": [None]},
    )

    assert grid.data[(-77.8, 166.7)] == {}
    assert conditions(grid, 0) == {}


@pytest.mark.asyncio
async def test_marine_only_hours_are_available_when_weather_is_empty():
    grid, _ = await fetch_grid({}, {"time": TIMES[:1], "wave_height": [0]})

    assert conditions(grid, 0) == {"wave_height": 0.0}
