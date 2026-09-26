# Architecture Dependency Graph

## High-Level Flow
`Frontend (React)` -> `FastAPI Routes (/api/v1/routes)` -> `RouteOrchestrator` -> `Providers (Vessel, Port, Iceberg)` -> `ML Models / Risk / Navigability` -> `A* Router` -> `RouteValidator` -> `PostgreSQL (if available)`

## Dependency Map

### Frontend
- Dependencies: React, Vite, MapLibre, Tailwind, Lucide React
- Flow: `Home.tsx` -> `OffshoreMap.tsx` -> Backend API `/api/v1/routes/plan`
- Note: High use of Demo Mode configurations.

### Backend APIs (`backend/app/api/v1/endpoints/`)
- `routes.py`: Depends on `astar_planner.plan_route()`, heavily utilizes `DEMO_MODE`.
- `vessels.py`, `icebergs.py`: Depends on settings, fallback to demo lists if `DEMO_MODE` is active.

### Services (`backend/app/services/`)
- `routing/astar.py`: Depends on Risk grid, candidate icebergs, vessel profile.
- `risk/engine.py`: Depends on Iceberg positions, Sea-Ice data, weights.
- `icebergs/` & `sea_ice/`: Depends on mock adapters if not using live data.

### ML Models
- `seaice_xgboost`: Loads from `mlops/` or `data/` artifacts.
- `trajectory_lstm`: Predicts displacements.

### Database
- SQLAlchemy Models -> `backend/app/db/`
- Demo Mode currently bypasses the DB if PostGIS is not available.

## Identified Issues
- **Circular Dependencies**: None detected at module level, but heavy coupling between API routes and `astar_planner`.
- **Hidden Coupling**: Demo mode checks inside core routing logic.
- **Inappropriate Dependency Direction**: API endpoints handling business logic for demo fallbacks.
