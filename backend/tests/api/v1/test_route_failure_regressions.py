"""Exercise the UI's comparison endpoint for the two reported port pairs."""

import math
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.config.config import settings
from app.services.routing.grid import GridBuilder, Node
from app.services.routing.validator import route_validator


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "origin,destination,minimum_distance",
    [
        pytest.param("166.67,-77.84", "115.74,-32.05", 3_000, id="mcmurdo-fremantle"),
        pytest.param("-68.13,-67.57", "-89.87,13.58", 5_000, id="rothera-acajutla"),
    ],
)
async def test_safety_first_comparison_for_reported_port_pairs(
    client, monkeypatch, origin, destination, minimum_distance,
):
    import app.services.environment.forecast_grid as forecast_module

    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(settings, "DEMO_CORRIDOR_ENABLED", False)
    monkeypatch.setattr(settings, "SYNTHETIC_DATA_MODE", True)

    def partial_conditions(lat, lon, target_time):
        # Keep the legacy null samples deliberately: the complete planner and
        # comparison pipeline must remain robust even before ingestion filters.
        return {
            "wave_height": 2.0 if lat > -45.0 else None,
            "wind_speed_10m": None,
            "wind_direction_10m": None,
            "ocean_current_velocity": None,
            "ocean_current_direction": None,
            "sea_ice_concentration": None,
        }

    monkeypatch.setattr(
        forecast_module,
        "global_forecast_grid",
        SimpleNamespace(prefetch_corridor=AsyncMock(), get_conditions=partial_conditions),
    )

    response = await client.post(
        "/api/v1/routes/compare",
        json={
            "origin": origin,
            "destination": destination,
            # Bundled RV Polarstern: no mocked vessel or planner is required.
            "vessel_id": "893c5286-9a2f-4e08-9df2-51a84f3ab6ba",
            "departure_time": "2026-09-13T12:00:00Z",
            "objective_type": "safest",
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    recommended = data["recommended_route"]
    assert recommended["properties"]["objective_type"] == "safest"
    assert recommended["properties"]["distance"] > minimum_distance
    assert recommended["properties"]["risk_data_status"] == "KNOWN"
    assert len(data["alternatives"]) == 3
    assert data["risk_factors"] == {"average_wave_height": 2.0}

    grid = GridBuilder(resolution=0.5)
    origin_lon, origin_lat = map(float, origin.split(","))
    goal_lon, goal_lat = map(float, destination.split(","))
    start = grid.snap_to_water(Node(origin_lat, origin_lon))
    goal = grid.snap_to_water(Node(goal_lat, goal_lon))
    assert start is not None and goal is not None
    assert recommended["geometry"]["coordinates"][0] == [start.lon, start.lat]
    assert recommended["geometry"]["coordinates"][-1] == [goal.lon, goal.lat]

    for feature in [recommended] + [alt["route"] for alt in data["alternatives"]]:
        properties = feature["properties"]
        for key in ("distance", "travel_time", "estimated_fuel"):
            assert math.isfinite(properties[key]) and properties[key] > 0
        coordinates = feature["geometry"]["coordinates"]
        assert len(coordinates) > 2
        wkt = "LINESTRING(" + ", ".join(f"{lon} {lat}" for lon, lat in coordinates) + ")"
        valid, error, details = route_validator.validate_wkt_linestring(wkt, strict=False)
        assert valid, f"Invalid {properties['objective_type']} route: {error}; {details}"
