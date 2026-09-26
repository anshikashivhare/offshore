# Full Project Diagnostic Report — SIH PS 26059

## Executive Summary
This diagnostic report evaluates the SIH-26059 repository (AI-Enabled Antarctic Sea-Ice, Iceberg Trajectory, and Navigation Decision Support System). The system is highly reliant on `DEMO_MODE` and fallback configurations which bypass critical production data paths. Several architectural leaks were identified where demo/fallback logic bleeds into core routing algorithms.

## Repository Inventory
- **backend**: Contains FastAPI, A* routing, risk engine, adapters.
- **frontend**: React/Vite, MapLibre based UI.
- **mlops/ml**: Contains XGBoost and LSTM training and monitoring scripts.
- **tests**: Contains pytest test suite, frequently relying on synthetic data.
- **docs**: Extensive phase documentation, architecture plans, and diagnostics.
- See `PROJECT_FILE_INVENTORY.md` for a complete list.

## Actual Architecture & Dependency Graph
See `ARCHITECTURE_DEPENDENCY_GRAPH.md`.
The orchestrator is bypassed frequently in API routes depending on the `DEMO_MODE` flag.

## Route Execution Trace
See `ACTUAL_ROUTE_EXECUTION_FLOW.md`.
The path uses hardcoded responses in demo mode and relies heavily on fallbacks when ML models fail to load or predict.

## Demo Leakage Audit
- **Critical Leak**: `backend/app/api/v1/endpoints/routes.py` explicitly injects `DEMO_MODE` into the `astar_planner`. This means the core routing algorithm is aware of the demo state, violating abstraction.
- Mock adapters exist in `backend/app/ingestion/adapters/` (e.g. `mock_nsidc`, `mock_era5`).
- The frontend relies on mock data files (`frontend/src/lib/offshore-mock-data.ts`).

## Silent-Fallback Audit
- When fetching ML outputs or risk data, failures (exceptions or missing data) often result in a default `risk = 0` or `fallback=None` which behaves as clear water. This is highly unsafe for a maritime navigation system.

## ML Audit & Monte Carlo Audit
- **Sea-Ice**: Uses XGBoost for spatial grid prediction. The model loads default artifacts but training data usage in test suites uses `SYNTHETIC_PROTOTYPE` heavily, risking leakage.
- **Iceberg LSTM v002**: Reconstructs longitude from displacements. Synthetic datasets are deeply embedded in test cases (`tests/test_iceberg_pipeline.py`).
- **Monte Carlo**: Provides empirical uncertainty but falls back to deterministic inputs when demo modes are enabled.

## CPA/Geometry Audit
- GeoJSON coordinate inversion risks exist. Frontend relies on `[longitude, latitude]` but backend fallbacks occasionally inject `[0.0, 0.0]`. 
- Geometry calculations use Euclidean distance approximations in some risk grid computations rather than pure geodesic.

## Risk Audit
- **Policy Check**: Intended composite risk is `max(sea_ice_risk, iceberg_risk)`. However, defaults and fallbacks can override this to zero if a component is missing.

## A* Audit & Constraint Audit
- The A* algorithm has constraints evaluated within the cost function rather than rejected by a strict validator in some paths.

## Database Audit
- PostGIS dependencies exist (`geoalchemy2`, `pyogrio`), but connections are bypassed via `DEMO_MODE` flag.

## Frontend Audit
- `OffshoreMap.tsx` and `map-components.tsx` set default zoom/centers and rely on `setTimeout` fallbacks to handle loading errors.

## Performance, Concurrency, and Async
- API endpoints call blocking models (XGBoost/LSTM) synchronously inside async handlers in some paths.

## Testing & Scientific Integrity
- Tests heavily use mocks and synthetic datasets (e.g., `tests/test_full_astar.py` uses mock vessels and routes). Does not prove production readiness.

## Codebase Health Statuses
- **CORRECTNESS**: NEEDS ATTENTION (silent fallbacks risk safety)
- **ARCHITECTURE**: CRITICAL (Demo mode coupled deeply)
- **SECURITY**: GOOD (No glaring secrets found in initial sweep)
- **PERFORMANCE**: NEEDS ATTENTION (Blocking calls in async)
- **DATA**: CRITICAL (Synthetic data throughout)
- **ML**: NEEDS ATTENTION
- **ROUTING**: NEEDS ATTENTION
- **API**: NEEDS ATTENTION
- **FRONTEND**: GOOD
- **TESTING**: CRITICAL (Mocks validate mocks)
- **REPRODUCIBILITY**: NEEDS ATTENTION
- **DOCUMENTATION**: GOOD (Extensively documented)
