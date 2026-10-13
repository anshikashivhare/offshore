"""Regressions for long-haul searches whose snapped ports have confined exits."""

import math
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from app.config.config import settings
from app.models.enums import ObjectiveType
from app.models.vessel import Vessel
from app.schemas.route import RouteRequest
from app.services.providers.synthetic_files import build_synthetic_risk_grid
from app.services.routing.astar import AStarRoutePlanner
from app.services.routing.dijkstra import DijkstraShortestPlanner
from app.services.routing.grid import Node
from app.services.routing.validator import route_validator


PLANNERS = [
    pytest.param(AStarRoutePlanner, "_grid_for_voyage", id="astar"),
    pytest.param(DijkstraShortestPlanner, "_search_grid_for_voyage", id="dijkstra"),
]


@pytest.mark.parametrize("planner_type,selector_name", PLANNERS)
@pytest.mark.parametrize("isolated_endpoint", ["origin", "destination"])
@pytest.mark.parametrize(
    "goal_lon,isolated_resolutions,expected_resolution",
    [
        pytest.param(90.0, (2.0,), 1.0, id="coarse-to-medium"),
        pytest.param(90.0, (2.0, 1.0), 0.5, id="coarse-through-medium-to-fine"),
        pytest.param(45.0, (1.0,), 0.5, id="medium-to-fine"),
    ],
)
def test_search_grid_falls_back_when_either_endpoint_is_isolated(
    monkeypatch, planner_type, selector_name, isolated_endpoint,
    goal_lon, isolated_resolutions, expected_resolution,
):
    planner = planner_type(resolution=0.5)
    start, goal = Node(0.0, 0.0), Node(0.0, goal_lon)
    isolated_node = start if isolated_endpoint == "origin" else goal

    # Only the geographic neighbor boundary is stubbed: the real distance
    # thresholds and each planner's resolution-selection rule are exercised.
    for grid in (planner.grid_builder, planner._medium_grid, planner._coarse_grid):
        def neighbors(node, *, resolution=grid.resolution):
            if node == isolated_node and resolution in isolated_resolutions:
                return []
            return [Node(node.lat + resolution, node.lon)]

        monkeypatch.setattr(grid, "get_neighbors", neighbors)

    selected = getattr(planner, selector_name)(start, goal)

    assert selected.resolution == expected_resolution


@pytest.mark.parametrize("planner_type,selector_name", PLANNERS)
@pytest.mark.parametrize(
    "goal_lon,expected_resolution",
    [
        pytest.param(10.0, 0.5, id="short-voyage-stays-fine"),
        pytest.param(45.0, 1.0, id="medium-voyage-keeps-medium"),
        pytest.param(90.0, 2.0, id="long-voyage-keeps-coarse"),
    ],
)
def test_search_grid_retains_largest_eligible_resolution_with_neighbors(
    monkeypatch, planner_type, selector_name, goal_lon, expected_resolution,
):
    planner = planner_type(resolution=0.5)
    start, goal = Node(0.0, 0.0), Node(0.0, goal_lon)
    for grid in (planner.grid_builder, planner._medium_grid, planner._coarse_grid):
        monkeypatch.setattr(
            grid, "get_neighbors", lambda node: [Node(node.lat + 0.5, node.lon)]
        )

    selected = getattr(planner, selector_name)(start, goal)

    assert selected.resolution == expected_resolution


@pytest.mark.parametrize("planner_type,selector_name", PLANNERS)
@pytest.mark.parametrize("coarse_isolated_endpoint", ["origin", "destination"])
def test_each_candidate_must_have_neighbors_at_both_endpoints(
    monkeypatch, planner_type, selector_name, coarse_isolated_endpoint,
):
    planner = planner_type(resolution=0.5)
    start, goal = Node(0.0, 0.0), Node(0.0, 90.0)
    coarse_isolated = start if coarse_isolated_endpoint == "origin" else goal
    medium_isolated = goal if coarse_isolated_endpoint == "origin" else start
    monkeypatch.setattr(
        planner._coarse_grid, "get_neighbors",
        lambda node: [] if node == coarse_isolated else [Node(1.0, node.lon)],
    )
    monkeypatch.setattr(
        planner._medium_grid, "get_neighbors",
        lambda node: [] if node == medium_isolated else [Node(1.0, node.lon)],
    )
    monkeypatch.setattr(
        planner.grid_builder, "get_neighbors", lambda node: [Node(0.5, node.lon)]
    )

    selected = getattr(planner, selector_name)(start, goal)

    assert selected.resolution == 0.5


@pytest.fixture
def offline_forecast(monkeypatch):
    import app.services.environment.forecast_grid as forecast_module

    monkeypatch.setattr(settings, "DEMO_MODE", False)
    monkeypatch.setattr(
        forecast_module,
        "global_forecast_grid",
        SimpleNamespace(prefetch_corridor=AsyncMock(), get_conditions=lambda *_: {}),
    )


@pytest.fixture
def research_vessel():
    return Vessel(
        vessel_id=UUID("00000000-0000-0000-0000-000000000001"),
        vessel_name="Confined port regression vessel",
        vessel_type="Research",
        cruising_speed=12.0,
        fuel_consumption=50.0,
        ice_capability="PC3",
        operational_limits={},
    )


@pytest.fixture(scope="module")
def synthetic_risk_grid():
    grid = build_synthetic_risk_grid()
    assert grid, "Bundled synthetic risk data must be available for Safety First"
    return grid


def safety_first_request(vessel, origin, destination):
    return RouteRequest(
        origin=origin,
        destination=destination,
        vessel_id=vessel.vessel_id,
        departure_time=datetime(2026, 9, 13, 12, tzinfo=timezone.utc),
        objective_type=ObjectiveType.SAFEST,
    )


def port_node(lonlat):
    lon, lat = map(float, lonlat.split(","))
    return Node(lat, lon)


@pytest.mark.asyncio
async def test_astar_chooses_search_resolution_after_snapping(
    offline_forecast, research_vessel, synthetic_risk_grid,
):
    planner = AStarRoutePlanner(resolution=0.5)
    # In open Atlantic water, fine-grid snapping crosses the medium-grid
    # distance threshold. Choosing from raw coordinates would use 0.5 degrees.
    request = safety_first_request(research_vessel, "-20,0.24", "-20,33.26")
    raw_start, raw_goal = port_node(request.origin), port_node(request.destination)
    snapped_start = planner.grid_builder.snap_to_water(raw_start)
    snapped_goal = planner.grid_builder.snap_to_water(raw_goal)
    assert snapped_start is not None
    assert snapped_goal is not None
    assert raw_start.distance_to(raw_goal) < 2_000
    assert snapped_start.distance_to(snapped_goal) >= 2_000

    route = await planner.plan_route(
        request, research_vessel, synthetic_risk_grid, demo_mode=False
    )

    first, second = route.waypoints[:2]
    assert max(abs(second.lat - first.lat), abs(second.lon - first.lon)) == 1.0
    assert Node(first.lat, first.lon) == snapped_start
    assert Node(route.waypoints[-1].lat, route.waypoints[-1].lon) == snapped_goal


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "origin,destination,minimum_distance",
    [
        pytest.param("-68.13,-67.57", "-89.87,13.58", 5_000, id="rothera-acajutla"),
        pytest.param("166.67,-77.84", "115.74,-32.05", 3_000, id="mcmurdo-fremantle"),
    ],
)
async def test_non_demo_safety_first_route_from_confined_port(
    offline_forecast, research_vessel, synthetic_risk_grid,
    origin, destination, minimum_distance,
):
    planner = AStarRoutePlanner(resolution=0.5)
    request = safety_first_request(research_vessel, origin, destination)
    snapped_start = planner.grid_builder.snap_to_water(port_node(origin))
    snapped_goal = planner.grid_builder.snap_to_water(port_node(destination))
    assert snapped_start is not None
    assert snapped_goal is not None

    # Exercise the production search with the actual land mask and bundled
    # risk surface; only the external forecast boundary is replaced.
    route = await planner.plan_route(
        request, research_vessel, synthetic_risk_grid, demo_mode=False
    )

    assert planner._grid_for_voyage(snapped_start, snapped_goal).resolution == 1.0
    assert route.objective_type == ObjectiveType.SAFEST
    assert route.risk_data_status == "KNOWN"
    assert len(route.waypoints) > 2
    assert Node(route.waypoints[0].lat, route.waypoints[0].lon) == snapped_start
    assert Node(route.waypoints[-1].lat, route.waypoints[-1].lon) == snapped_goal
    # The actual search must use the medium lattice, not just choose it when
    # queried separately.
    first, second = route.waypoints[:2]
    first_step = max(abs(second.lat - first.lat), abs(second.lon - first.lon))
    assert first_step == pytest.approx(1.0)
    assert route.distance > minimum_distance
    for metric in (route.distance, route.travel_time, route.estimated_fuel):
        assert math.isfinite(metric) and metric > 0
    assert route.eta > request.departure_time
    assert route.travel_time == pytest.approx(
        route.distance / research_vessel.cruising_speed
    )
    assert route.estimated_fuel == pytest.approx(
        route.travel_time * research_vessel.fuel_consumption
    )
    assert math.isfinite(route.risk_score) and 0 <= route.risk_score < 0.9
    assert math.isfinite(route.risk_exposure) and route.risk_exposure >= 0

    valid, error, details = route_validator.validate_wkt_linestring(
        route.geometry, strict=False
    )
    assert valid, f"Route failed independent land validation: {error}; {details}"


@pytest.mark.asyncio
async def test_unconditional_coarse_grid_reproduces_rothera_search_failure(
    monkeypatch, offline_forecast, research_vessel, synthetic_risk_grid,
):
    planner = AStarRoutePlanner(resolution=0.5)
    request = safety_first_request(
        research_vessel, "-68.13,-67.57", "-89.87,13.58"
    )
    snapped_start = planner.grid_builder.snap_to_water(port_node(request.origin))
    snapped_goal = planner.grid_builder.snap_to_water(port_node(request.destination))
    assert snapped_start == Node(-67.5, -68.0)
    assert snapped_goal == Node(13.5, -90.0)
    assert planner.grid_builder.get_neighbors(snapped_start)
    assert planner._medium_grid.get_neighbors(snapped_start)
    assert not planner._coarse_grid.get_neighbors(snapped_start)
    assert planner._coarse_grid.get_neighbors(snapped_goal)

    # Reintroduce only the old resolution choice, keeping land/risk checks
    # and the actual snapped port coordinates intact.
    monkeypatch.setattr(planner, "_grid_for_voyage", lambda *_: planner._coarse_grid)
    with pytest.raises(
        ValueError, match="No feasible route exists within the configured search limits"
    ):
        await planner.plan_route(
            request, research_vessel, synthetic_risk_grid, demo_mode=False
        )
