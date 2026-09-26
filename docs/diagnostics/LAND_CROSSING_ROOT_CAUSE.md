# Land Crossing Root Cause Analysis

## 1. Exact component generating the invalid route
There are two distinct components contributing to land-crossing routes:
1. **Backend (`astar.py`)**: The A* termination condition allows a direct unvalidated jump to the goal node if the distance is `< 1.5 * resolution` (which is up to 45 NM on a 0.5° grid). `_reconstruct_route` adds the `goal_node` to the path unconditionally. If this unvalidated segment crosses land, the `RouteValidator` in `routes.py` catches it and throws an HTTP 500 Error.
2. **Frontend (`NavigationMode.tsx`)**: When the backend API fails (such as returning a 500 error due to the land-crossing bug above, or general unavailability), the frontend uses a fallback: `generateGreatCircleWaypoints(origin, destination, 35)`. This creates a fake "mock" geometry directly between the origin and destination, completely ignoring land, which is what the user visually sees.

## 2. Whether land masking is node-only, edge-based, or both
- `grid.py` has edge-based sampling in `_get_valid_neighbors`.
- However, `astar.py` creates a final edge bypassing `grid.py` entirely.

## 3. Grid resolution
- The global search grid uses 0.5 degrees resolution.

## 4. Neighbor connectivity (4/8/etc.)
- 8-neighbor connectivity is generated via `[-step, 0, step]` loops in `_get_valid_neighbors`.

## 5. Whether diagonal edges are allowed
- Diagonal edges are allowed and checked for land using dense sampling in `grid.py`.

## 6. Whether edge geometry is sampled/interpolated
- Yes, `grid.py` samples the edge every 0.05 degrees.

## 7. Whether land checks use
- A raster mask via the `global_land_mask` PyPI package (`globe.is_land()`).

## 8. Whether RouteValidator independently checks land intersection
- Yes, `RouteValidator` in `validator.py` independently verifies all segments. 
- In `routes.py`, `route_validator.validate_wkt_linestring` is called. If it fails, it raises an HTTP 500 error.

## 9. Whether frontend transforms longitude/latitude incorrectly
- No, the issue is not coordinate inversion, but fallback geometry creation.

## 10. Whether antimeridian handling contributes to the issue
- Not the primary cause of this bug, though antimeridian crossings are handled by shortening the `dlon`.

## 11. Whether origin/destination snapping can place endpoints incorrectly
- The grid builder snaps ports to water within a 3.0-degree radius, which is usually correct but large.

## 12. Whether any mock/fallback geometry is still bypassing backend output
- Yes, heavily. `NavigationMode.tsx` uses `generateGreatCircleWaypoints(origin, destination, 35)` if `route.geometry` is empty.
