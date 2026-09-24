from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4
import math

import pytest
from global_land_mask import globe

from app.models.enums import ObjectiveType
from app.models.vessel import Vessel
from app.schemas.route import RouteRequest
from app.services.routing.astar import AStarRoutePlanner
from app.services.routing.grid import Node


@pytest.mark.asyncio
async def test_long_haul_route_uses_a_coarser_water_checked_grid(monkeypatch):
    # Avoid an external forecast dependency; this test exercises geographic
    # search resolution and land avoidance only.
    import app.services.environment.forecast_grid as forecast_module

    monkeypatch.setattr(
        forecast_module,
        "global_forecast_grid",
        SimpleNamespace(prefetch_corridor=AsyncMock(), get_conditions=lambda *_: {}),
    )
    vessel = Vessel(
        vessel_id=uuid4(),
        vessel_name="Test vessel",
        vessel_type="Research",
        cruising_speed=12.0,
        fuel_consumption=50.0,
        ice_capability="PC3",
    )
    request = RouteRequest(
        origin="-45.03,-60.73",  # Ellefsen Harbor, Antarctica
        destination="-13.43,27.08",  # Laayoune, Western Sahara
        vessel_id=vessel.vessel_id,
        departure_time=datetime.now(timezone.utc),
        objective_type=ObjectiveType.SAFEST,
    )

    planner = AStarRoutePlanner(resolution=0.5)
    route = await planner.plan_route(request, vessel, risk_grid={}, demo_mode=True)

    assert planner._grid_for_voyage(Node(-60.73, -45.03), Node(27.08, -13.43)).resolution == 2.0
    # The route is a valid multi-thousand-nautical-mile ocean passage rather
    # than a failed search; exact distance depends on port snapping/grid cells.
    assert route.distance > 5_000

    for current, neighbor in zip(route.waypoints, route.waypoints[1:]):
        dlat, dlon = neighbor.lat - current.lat, neighbor.lon - current.lon
        if dlon > 180:
            dlon -= 360
        elif dlon < -180:
            dlon += 360
        samples = max(5, math.ceil(math.hypot(dlat, dlon) / 0.05))
        for index in range(samples + 1):
            fraction = index / samples
            lat = current.lat + fraction * dlat
            lon = current.lon + fraction * dlon
            if lon > 180:
                lon -= 360
            elif lon < -180:
                lon += 360
            assert not globe.is_land(lat, lon)
