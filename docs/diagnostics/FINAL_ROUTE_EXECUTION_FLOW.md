# Final Route Execution Flow

## Overview
The route execution path is initiated via an API POST request and orchestrates multiple spatial, environmental, and routing modules.

## Stage-by-Stage Trace

1. **Request Reception:** 
   - `backend/app/api/v1/endpoints/routes.py::plan_route`
   - Receives payload and validates standard inputs against `RouteRequest` schema.

2. **Vessel Resolution:**
   - `backend/app/api/v1/endpoints/routes.py::plan_route`
   - Fetches vessel from PostgreSQL via `vessel_repo.get(db, request.vessel_id)`.

3. **Origin/Destination Resolution & Snapping:**
   - `backend/app/api/v1/endpoints/routes.py::plan_route`
   - Parses coordinates and calls `astar_planner.grid_builder.snap_to_water`.
   - If origin/destination is on land and no navigable water is within 3.0 degrees, returns HTTP 400.

4. **Risk Grid Resolution (Environmental Context):**
   - `backend/app/api/v1/endpoints/routes.py::_build_risk_grid`
   - Executes PostGIS query (`ST_Intersects`) over the bounding box to fetch `RiskCell` records.
   - Converts the ML predictions and weather context into a discrete dict-of-floats grid.

5. **Iceberg Candidates Resolution:**
   - *Currently Not Fully Integrated into API Path.*
   - `backend/app/services/providers/postgres_providers.py::PostGISIcebergProvider` exists but is bypassed in the raw `astar_planner` direct call.

6. **A* Execution:**
   - `backend/app/services/routing/astar.py::AStarRoutePlanner.plan_route`
   - Instantiates nodes and evaluates candidate edges using spatial grid calculations (`grid_builder.py`).
   - Retrieves cost for edges leveraging heuristic optimization.
   - Enforces exact goal termination without proximity bypass.

7. **Final Validation:**
   - `backend/app/services/routing/validator.py::RouteValidator.validate_wkt_linestring`
   - Evaluates the final generated geometry LineString segment by segment to ensure 0 land intersections.

8. **API Response:**
   - `backend/app/api/v1/endpoints/routes.py::plan_route`
   - Converts the DB/domain model to GeoJSON Feature response.
