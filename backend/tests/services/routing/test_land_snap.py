import pytest
from app.services.routing.grid import GridBuilder, Node

def test_snap_to_water():
    builder = GridBuilder(resolution=0.5)

    # Land node (McMurdo)
    mcmurdo = Node(lat=-77.84, lon=166.67)
    snapped_mc = builder.snap_to_water(mcmurdo, max_radius_degrees=2.0)
    assert snapped_mc is not None
    assert snapped_mc != mcmurdo
    # Check it is on the grid (multiples of 0.5)
    assert snapped_mc.lat % 0.5 == 0
    assert snapped_mc.lon % 0.5 == 0

    # Deep interior Antarctica (South Pole)
    interior = Node(lat=-89.0, lon=0.0)
    snapped_int = builder.snap_to_water(interior, max_radius_degrees=2.0)
    assert snapped_int is None
