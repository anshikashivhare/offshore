# Actual Route Execution Flow

## Overview
This document traces the actual path of a route calculation from the frontend HTTP request through the backend processing and back to the response.

## Trace Path

1. **HTTP Request**
   - **Endpoint**: `POST /api/v1/routes/plan`
   - **Payload**: Contains origin, destination, vessel config, routing preferences.

2. **Request Schema & Validation**
   - **Module**: `backend/app/schemas/route.py`
   - **Action**: Validates coordinates, vessel ID, time constraints.

3. **API Handler**
   - **Module**: `backend/app/api/v1/endpoints/routes.py`
   - **Action**: Checks for `DEMO_MODE`. If active, skips database validation and injects demo data.
   - **Logic Leak**: The API handler contains business logic that decides whether to hit the DB or use fallbacks, rather than delegating this entirely to an orchestrator.

4. **Route Orchestrator / Planner**
   - **Module**: `backend/app/services/routing/astar.py` (and caller)
   - **Action**: Initializes A* state. Receives candidate icebergs and risk grids.

5. **Providers (Vessels, Ports, Icebergs)**
   - **Modules**: `backend/app/api/v1/endpoints/vessels.py`, `backend/app/api/v1/endpoints/icebergs.py`
   - **Action**: In Demo Mode, these return static hard-coded dictionaries (e.g., "demo-hazard").

6. **Forecast & ML**
   - **Sea-Ice**: Pre-computed grids or loaded via XGBoost if predicting dynamically. Often mocked in tests.
   - **Iceberg (LSTM)**: Fetches LSTM predictions. If unavailable, falls back to synthetic data.

7. **Risk & Navigability**
   - **Module**: `backend/app/services/risk/engine.py`
   - **Action**: Computes composite risk (e.g. `max(sea_ice_risk, iceberg_risk)`).
   - **Issue**: Silent zero-risk fallbacks exist if data is unavailable (e.g., `Exception` caught -> `risk = 0`).

8. **A* Execution**
   - **Module**: `backend/app/services/routing/astar.py` -> `calculate_edge_cost_4d()`
   - **Action**: Calculates cost based on distance + risk * gamma + time.

9. **Route Validator**
   - **Module**: Usually tightly coupled with A*.
   - **Action**: Checks hard constraints (land avoidance).

10. **Persistence**
    - **Module**: DB Session.
    - **Action**: Bypassed if `DEMO_MODE=True`.

11. **Response Schema**
    - **Module**: `backend/app/schemas/route.py` -> `RouteResponse`
    - **Action**: Returns path, total distance, risk metrics, ETA.

## Provenance & Errors
- Errors in fetching ML data or risk components often lead to default `0` risk (fallback behavior) rather than hard failures, which is dangerous in a production routing system.
