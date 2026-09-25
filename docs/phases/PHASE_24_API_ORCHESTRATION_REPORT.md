# PHASE 24: BACKEND ORCHESTRATION + API INTEGRATION
**Project:** SIH 26059 - Antarctic Navigation

## 1. Orchestration Architecture
The backend routing logic has been successfully decoupled into `RouteOrchestrator` (`backend/app/services/orchestration/route_orchestrator.py`).
The exact request flow is:
```text
POST /api/v1/routes/plan
    ↓
vessel resolution (PostgreSQL or fallback to Demo JSON)
    ↓
RouteOrchestrator.execute_route_plan()
    ↓
_prepare_forecast_context() -> Sea-Ice / Weather Grid
    ↓
_prepare_iceberg_context() -> ST_Intersects / Candidate Array
    ↓
AStarRoutePlanner.plan_route(context)
    ↓
RouteValidator (independent geometric cross-check)
    ↓
Metadata / Provenance Population
    ↓
RouteCreate -> RouteResponse (GeoJSON)
```

## 2. API Contract & Response Schema
The `RouteRequest` and `RouteResponse` objects inherently support explicit provenance fields, rather than unstructured dictionaries.
- `candidate_icebergs`, `iceberg_model_version`, `iceberg_forecast_available`, and `forecast_coverage_hours` are explicitly written.
- Unavailability maps to `UNKNOWN` or `UNAVAILABLE` strings, never silently defaulting to `0.0` risk logic at the orchestration layer.

## 3. DEMO_MODE Policy
The system preserves `DEMO_MODE`. 
If `DEMO_MODE=True`, the orchestrator explicitly injects:
```python
[{"iceberg_id": "demo-hazard", "lat": -60.05, "lon": 50.55, "source": "synthetic_demo"}]
```
This isolates the synthetic demonstration iceberg exactly to the single bounding-box array method expected by production logic, preventing internal `if demo_mode:` scattering throughout `astar.py` and PyTorch.

## 4. Failure Semantics & Route Validation
- The `RouteValidator` independently tests the `AStarRoutePlanner`'s output geometric LineString against land constraints. 
- If validation fails, `land_avoidance_validated=False` is set and warning messages are propagated. 
- The endpoint correctly returns HTTP 400 (Bad Request) for coordinate errors and HTTP 404 for missing DB vessels.

## 5. Model Provenance Rule
No data in this phase elevates the model to "scientifically validated". The ML models merely process synthetic training data to yield geometric costs. The orchestrator returns model versions (e.g., `v002`) indicating that the pipeline is *active*, not necessarily empirically proven.

## Required Status Matrix

| Component | Status |
| :--- | :--- |
| **API contract** | VERIFIED |
| **Orchestration** | VERIFIED |
| **Vessel resolution** | VERIFIED |
| **Forecast preparation** | VERIFIED |
| **Sea-ice integration** | VERIFIED |
| **Iceberg integration** | VERIFIED |
| **A* invocation** | VERIFIED |
| **RouteValidator invocation** | VERIFIED |
| **Provenance** | VERIFIED |
| **Error handling** | VERIFIED |
| **DEMO_MODE isolation** | VERIFIED |
| **Test coverage** | PARTIALLY VERIFIED (Script limits) |

**Conclusion:** Phase 24 completes the architectural wiring required to unify constraints, mathematical ML models, environmental data, and graph routing into a cohesive HTTP JSON API endpoint.
