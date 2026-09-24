import pytest
from app.services.routing.grid import GridBuilder, Node

import numpy as np

class MockGlobe:
    def is_land(self, lat, lon):
        # Handle numpy arrays or scalars
        return (np.abs(lat - (-60.5)) < 0.15) & (np.abs(lon - (-60.5)) < 0.15)

def test_segment_land_avoidance():
    # Monkeypatch the globe in grid.py
    import app.services.routing.grid
    original_globe = app.services.routing.grid.globe
    app.services.routing.grid.globe = MockGlobe()
    
    try:
        builder = GridBuilder(resolution=1.0)
        
        # Test 1: Node at -60, -60. Neighbor at -61, -61.
        # The midpoint is -60.5, -60.5, which is exactly the island. 
        # A midpoint check WOULD catch this.
        current = Node(lat=-60.0, lon=-60.0)
        app.services.routing.grid._get_valid_neighbors.cache_clear()
        neighbors = builder.get_neighbors(current)
        
        # Ensure (-61, -61) is NOT in neighbors
        assert not any(n.lat == -61.0 and n.lon == -61.0 for n in neighbors)
        
        # Test 2: Shift the island slightly so it's NOT at the midpoint, but still on the segment.
        class MockGlobeShifted:
            def is_land(self, lat, lon):
                # Island at -60.2, -60.2 (20% along the path)
                return (np.abs(lat - (-60.2)) < 0.15) & (np.abs(lon - (-60.2)) < 0.15)
                
        app.services.routing.grid.globe = MockGlobeShifted()
        app.services.routing.grid._get_valid_neighbors.cache_clear()
        
        neighbors = builder.get_neighbors(current)
        
        # If segment sampling is working (e.g. 5 samples), it should test t=0.2 and hit the island.
        # Ensure (-61, -61) is NOT in neighbors
        assert not any(n.lat == -61.0 and n.lon == -61.0 for n in neighbors)
        
    finally:
        # Restore globe
        app.services.routing.grid.globe = original_globe
