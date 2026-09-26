# Land Route Regression Tests

## Test Suite Location
Regression tests are located in `tests/test_land_crossing_regression.py`.

## Executed Tests
We implemented tests that enforce the invariant: `land_intersections == 0`. We use the `route_validator` to parse the output `Route.geometry` to verify that no node and no dense sample on any segment intersects land.

### 1. `test_ocean_to_ocean_no_land`
- **Scenario**: Valid ocean-to-ocean routing in open water.
- **Verification**: The route successfully computes a valid path, and the `route_validator.validate_wkt_linestring` returns zero land intersections.

### 2. `test_route_blocked_by_land`
- **Scenario**: Routing across an obstacle (the Antarctic Peninsula). 
- **Verification**: The route generation process must route AROUND the peninsula instead of jumping across it. The output `Route.geometry` is passed to `route_validator` which confirms zero land intersections.

### 3. `test_invalid_land_origin`
- **Scenario**: The requested origin is deep inland (e.g. `0.0, -85.0`) with no navigable water nearby.
- **Verification**: The system must explicitly reject routing, returning `None` from the water-snapping utility and propagating the failure correctly instead of generating a mock geometry.

## Test Execution
Tests can be executed by running:
```bash
export PYTHONPATH=$(pwd)/backend
source backend/venv_mac/bin/activate
pytest tests/test_land_crossing_regression.py
```
All tests pass successfully.
