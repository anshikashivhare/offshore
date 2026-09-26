# Demo Acceptance Report

## Status of the 4 Required Deterministic Demonstration Scenarios:

**Scenario A: Open ocean route**
- **Status:** PASSED (Verified via API E2E scripts producing valid geometry).

**Scenario B: Route constrained around land**
- **Status:** PASSED (Verified via Antarctic Peninsula transit).

**Scenario C: Safety-priority route with environmental/iceberg risk**
- **Status:** BLOCKED (Requires wiring `PostGISIcebergProvider` into the main A* `plan_route` hook within `routes.py`).

**Scenario D: Failure/warning scenario showing missing/unavailable data**
- **Status:** PASSED (Verified. Missing inland endpoints result in standard REST failures and gracefully surface error details).

## Demo Mode Usage
The `DEMO_MODE` environment variable fallback successfully serves synthetic endpoints if toggled on, but for the above demonstrations, the system was configured to interact dynamically via actual A* calculations without drawing fake geometries.
