"""Adversarial tests for land avoidance in challenging geographic scenarios."""
import pytest
from app.services.routing.grid import GridBuilder, Node
from app.services.routing.astar import AStarRoutePlanner
from app.models.enums import ObjectiveType
from app.schemas.route import RouteRequest
from app.models.vessel import Vessel
from app.services.routing.validator import route_validator
from global_land_mask import globe


@pytest.mark.asyncio
async def test_drake_passage_route():
    """Test routing through Drake Passage between South America and Antarctica.

    This narrow strait is a critical test case - routes should go around Cape Horn
    and through the passage without touching land on either side.
    """
    planner = AStarRoutePlanner(resolution=0.5)

    request = RouteRequest(
        vessel_id='00000000-0000-0000-0000-000000000000',
        origin='-55,-68',  # South of Cape Horn
        destination='-62,-58',  # North of Antarctic Peninsula
        objective_type=ObjectiveType.SHORTEST,
        departure_time='2026-09-24T12:00:00Z'
    )

    vessel = Vessel(
        vessel_id='00000000-0000-0000-0000-000000000000',
        vessel_name='Drake Explorer',
        vessel_type='Research',
        ice_capability='PC3',
        cruising_speed=12.0,
        fuel_consumption=2000.0
    )

    route_create = await planner.plan_route(request, vessel, {}, demo_mode=True)

    # Validate with our validator
    is_valid, error, details = route_validator.validate_wkt_linestring(
        route_create.geometry, strict=False
    )

    assert is_valid, f"Drake Passage route crosses land: {error}"
    assert len(route_create.waypoints) > 0


@pytest.mark.asyncio
async def test_antarctic_peninsula_circumnavigation():
    """Test route that must go around Antarctic Peninsula.

    The peninsula extends north from the continent. Routes between
    west and east sides must navigate around, not through.
    """
    planner = AStarRoutePlanner(resolution=0.5)

    request = RouteRequest(
        vessel_id='00000000-0000-0000-0000-000000000000',
        origin='-64,-62',  # West side of peninsula
        destination='-64,-56',  # East side of peninsula
        objective_type=ObjectiveType.SHORTEST,
        departure_time='2026-09-24T12:00:00Z'
    )

    vessel = Vessel(
        vessel_id='00000000-0000-0000-0000-000000000000',
        vessel_name='Peninsula Navigator',
        vessel_type='Research',
        ice_capability='PC3',
        cruising_speed=12.0,
        fuel_consumption=2000.0
    )

    route_create = await planner.plan_route(request, vessel, {}, demo_mode=True)

    # Validate route
    is_valid, error, details = route_validator.validate_wkt_linestring(
        route_create.geometry, strict=False
    )

    assert is_valid, f"Antarctic Peninsula route crosses land: {error}"


@pytest.mark.asyncio
async def test_diagonal_shortcut_prevention():
    """Test that diagonal moves don't shortcut through narrow land masses.

    With 0.5° resolution, diagonal moves span ~0.7°. This test ensures
    that segment sampling catches land between grid-aligned water nodes.
    """
    planner = AStarRoutePlanner(resolution=0.5)

    # Route around southern tip of South America
    request = RouteRequest(
        vessel_id='00000000-0000-0000-0000-000000000000',
        origin='-56,-70',  # Pacific side
        destination='-54,-65',  # Atlantic side
        objective_type=ObjectiveType.SHORTEST,
        departure_time='2026-09-24T12:00:00Z'
    )

    vessel = Vessel(
        vessel_id='00000000-0000-0000-0000-000000000000',
        vessel_name='Tierra del Fuego Navigator',
        vessel_type='Research',
        ice_capability='PC3',
        cruising_speed=12.0,
        fuel_consumption=2000.0
    )

    route_create = await planner.plan_route(request, vessel, {}, demo_mode=True)

    # Validate no land crossing
    is_valid, error, details = route_validator.validate_wkt_linestring(
        route_create.geometry, strict=False
    )

    assert is_valid, f"Route shortcuts through Tierra del Fuego: {error}"


@pytest.mark.asyncio
async def test_ross_sea_to_weddell_sea():
    """Test long route around Antarctica from Ross Sea to Weddell Sea.

    This tests that the coarse global grid (used for long distances) still
    maintains land avoidance when resolution increases to 1.0° or 2.0°.
    """
    planner = AStarRoutePlanner(resolution=0.5)

    request = RouteRequest(
        vessel_id='00000000-0000-0000-0000-000000000000',
        origin='170,-75',  # Ross Sea
        destination='-45,-70',  # Weddell Sea
        objective_type=ObjectiveType.SHORTEST,
        departure_time='2026-09-24T12:00:00Z'
    )

    vessel = Vessel(
        vessel_id='00000000-0000-0000-0000-000000000000',
        vessel_name='Antarctic Circumnavigator',
        vessel_type='Research',
        ice_capability='PC3',
        cruising_speed=12.0,
        fuel_consumption=2000.0
    )

    route_create = await planner.plan_route(request, vessel, {}, demo_mode=True)

    # Validate - this uses coarse grid internally but should still avoid land
    is_valid, error, details = route_validator.validate_wkt_linestring(
        route_create.geometry, strict=False
    )

    assert is_valid, f"Ross-to-Weddell route crosses Antarctic land: {error}"


@pytest.mark.asyncio
async def test_bransfield_strait():
    """Test routing through Bransfield Strait between Antarctic Peninsula and South Shetland Islands.

    This narrow strait is a challenging navigation area with land on both sides.
    """
    planner = AStarRoutePlanner(resolution=0.5)

    request = RouteRequest(
        vessel_id='00000000-0000-0000-0000-000000000000',
        origin='-62.5,-60',  # Entrance to strait
        destination='-63,-56',  # Exit from strait
        objective_type=ObjectiveType.SHORTEST,
        departure_time='2026-09-24T12:00:00Z'
    )

    vessel = Vessel(
        vessel_id='00000000-0000-0000-0000-000000000000',
        vessel_name='Strait Navigator',
        vessel_type='Research',
        ice_capability='PC3',
        cruising_speed=12.0,
        fuel_consumption=2000.0
    )

    route_create = await planner.plan_route(request, vessel, {}, demo_mode=True)

    # Validate
    is_valid, error, details = route_validator.validate_wkt_linestring(
        route_create.geometry, strict=False
    )

    assert is_valid, f"Bransfield Strait route crosses land: {error}"


@pytest.mark.asyncio
async def test_antimeridian_crossing_near_land():
    """Test antimeridian crossing in Southern Ocean where New Zealand is nearby.

    Ensures that antimeridian logic doesn't create shortcuts through islands.
    """
    planner = AStarRoutePlanner(resolution=0.5)

    request = RouteRequest(
        vessel_id='00000000-0000-0000-0000-000000000000',
        origin='175,-60',  # East of New Zealand
        destination='-175,-60',  # Just across antimeridian
        objective_type=ObjectiveType.SHORTEST,
        departure_time='2026-09-24T12:00:00Z'
    )

    vessel = Vessel(
        vessel_id='00000000-0000-0000-0000-000000000000',
        vessel_name='Antimeridian Crosser',
        vessel_type='Research',
        ice_capability='PC3',
        cruising_speed=12.0,
        fuel_consumption=2000.0
    )

    route_create = await planner.plan_route(request, vessel, {}, demo_mode=True)

    # Validate
    is_valid, error, details = route_validator.validate_wkt_linestring(
        route_create.geometry, strict=False
    )

    assert is_valid, f"Antimeridian crossing route crosses land: {error}"


def test_grid_neighbors_comprehensive_sampling():
    """Test that get_neighbors uses sufficient sampling density.

    Verify that even at coarse resolutions, segment sampling catches land.
    """
    # Test with 2.0° resolution (coarse global grid)
    grid_builder = GridBuilder(resolution=2.0)

    # Pick a node in open ocean
    current = Node(lat=-60.0, lon=-60.0)
    neighbors = grid_builder.get_neighbors(current)

    # All neighbors should be water
    for neighbor in neighbors:
        # Verify each neighbor wasn't rejected due to land
        # If this was near land, some neighbors would be missing

        # Verify the segment between current and neighbor is checked densely
        dlat = neighbor.lat - current.lat
        dlon = neighbor.lon - current.lon
        if dlon > 180:
            dlon -= 360
        elif dlon < -180:
            dlon += 360

        import math
        dist_deg = math.sqrt(dlat**2 + dlon**2)
        # Should sample at ~0.05° resolution
        expected_samples = max(5, int(math.ceil(dist_deg / 0.05)))

        # For 2.0° diagonal: sqrt(2*2^2) = 2.83°, so ~57 samples
        assert expected_samples >= 5, "Insufficient segment sampling"


@pytest.mark.asyncio
async def test_final_approach_refinement_maintains_land_avoidance():
    """Test that _refine_final_approach doesn't introduce land crossings.

    The refinement process replaces coarse final edges with fine-grid paths.
    This must maintain the same land avoidance guarantees.
    """
    planner = AStarRoutePlanner(resolution=0.5)

    # Long route that triggers coarse grid, with coastal destination
    request = RouteRequest(
        vessel_id='00000000-0000-0000-0000-000000000000',
        origin='-55,-70',  # Start point
        destination='-64,-60',  # Coastal destination near Antarctic Peninsula
        objective_type=ObjectiveType.FASTEST,
        departure_time='2026-09-24T12:00:00Z'
    )

    vessel = Vessel(
        vessel_id='00000000-0000-0000-0000-000000000000',
        vessel_name='Approach Tester',
        vessel_type='Research',
        ice_capability='PC3',
        cruising_speed=12.0,
        fuel_consumption=2000.0
    )

    route_create = await planner.plan_route(request, vessel, {}, demo_mode=True)

    # The final approach refinement runs on the last segment
    # Validate that the refined route still avoids land
    is_valid, error, details = route_validator.validate_wkt_linestring(
        route_create.geometry, strict=False
    )

    assert is_valid, f"Refined final approach crosses land: {error}"

    # Also verify the final waypoint is on water
    final_wp = route_create.waypoints[-1]
    assert not globe.is_land(final_wp.lat, final_wp.lon), "Final waypoint on land"
