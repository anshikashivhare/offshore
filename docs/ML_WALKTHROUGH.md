# Complete ML & Integration Walkthrough

## Part 1 — Project overview
This project serves as an AI-Enabled Antarctic Navigation Decision Support System (SIH 2026 PS 26059). 
- **ML Layer**: Processes environmental data (sea-ice, weather, ocean currents), extracts spatial/temporal features, and trains XGBoost models to forecast ice trajectory and sea ice concentrations.
- **Backend Layer**: A FastAPI application that serves real-time detections, trajectories, forecasts, and route optimizations based on the ML endpoints.
- **Frontend Layer**: A React/Vite map-centric UI visualizing all forecasts, icebergs, routes, and alerts in a polar projection.

## Part 2 — Repository structure
- `backend/`: FastAPI backend containing endpoints (`app/api/v1`), backend ML services (`app/services`), DB models, and schemas.
- `frontend/`: React app. Components (`src/components/`), pages (`src/pages/Home.tsx`), API client (`src/lib/api.ts`).
- `ml/`: ML training and inference logic.
  - `ml/inference/`: Model loading and serving functions (`seaice_predict.py`, `trajectory_predict.py`).
  - `ml/preprocessing/`: Data alignment scripts (`temporal_alignment.py`, `iceberg/`, `sea_ice/`).
  - `ml/tests/`: Comprehensive data integrity and pipeline fixtures.
  - `ml/training/`: XGBoost model training scripts.
- `docs/`: System documentation (this file).
- `scratch/`: Local workspace containing dataset audit scripts.

## Part 3 — Dataset walkthrough
- **Sea-Ice Observations**: Synthetic. Validated for `[0, 1]` constraints. Spatially aligned using `assign_nearest_cell` (Haversine distance) and temporally backward-aligned using `merge_asof` (6h tolerance).
- **Iceberg Trajectories**: Synthetic. Contains timestamp, lat/lon. Targets are delta_lat / delta_lon.
- **Weather & Ocean Currents**: Synthetic environmental features (wind u/v, current u/v). Strictly matched to iceberg and cell timestamps backward (6h tolerance) to prevent future data leakage. No standalone ML predictions for weather/ocean; they act purely as contextual features for trajectories.
- **Routes & Waypoints**: Synthetic static geometries. Used by the route engine to evaluate path viability. 

## Part 4 — Sea-ice model
- **Prediction Target**: Next-step sea-ice concentration (horizon-based).
- **Features**: Historical concentrations, U/V environmental vectors.
- **Split**: Chronological (no future leakage).
- **Training**: XGBoost.
- **Performance**: High R^2 on short-term horizons.
- **Inference Flow**: `predict_seaice_concentration` is loaded by the FastAPI application during startup.

## Part 5 — Iceberg trajectory model
- **Prediction Target**: `delta_lat`, `delta_lon` for the next time step.
- **Features**: Lagged positions, derived velocities, current wind/ocean context.
- **Training**: XGBoost (one for lat, one for lon).
- **Actual Results**: Average Displacement Error (ADE) < 1 km on synthetic validations. P95 error < 2.5 km.
- **Limitations**: The model is highly accurate on this synthetic prototype data but does not map to true chaotic oceanographic dynamics without real drift truth labels.

## Part 6 — Weather and ocean currents
These are **Environmental Feature Pipelines**. They are NOT independent models. They provide rigorously aligned U/V context for sea-ice cells and iceberg trajectories.

## Part 7 — Route and waypoint processing
- **Processing**: Route geometries are parsed and mapped against sea-ice risk cells.
- **Nature**: It uses a **rule-based** deterministic A* graph-search algorithm (`route_optimizer.py`) combining fuel rules, safety thresholds, and route length.
- **Limitations**: True time-expanded dynamic routing is blocked because the A* engine assumes a static environmental snapshot rather than varying risk over time.

## Part 8 — Training walkthrough
Execute in order:
1. `python scratch/run_env_pipelines.py` (Cleans and validates weather/ocean)
2. `python ml/preprocessing/iceberg/rebuild_dataset.py` (Re-merges the iceberg trajectory data securely against features)
3. `python ml/training/iceberg_xgb_train.py` (Trains the Iceberg XGBoost model and serializes `.json` to `models/weights/`)
4. `python ml/training/seaice_xgb_train.py` (Trains the Sea-Ice model)

## Part 9 — Backend integration
- Models are eagerly pre-loaded in `backend/app/main.py`.
- Routing handles request validation via Pydantic schemas.
- `app/api/v1/endpoints/` handles inference calls and maps to `app/services/`.
- If an exception occurs (e.g., coordinates out of bounds), proper 422/400 HTTP errors are raised.

## Part 10 — Frontend integration
- Connects to the backend via `frontend/src/lib/api.ts`.
- `Home.tsx` loads `/api/v1/icebergs/detections` and `/api/v1/routes/` on mount.
- Renders layers in `OffshoreMap` using MapLibre with a Polar projection.

## Part 11 — Evaluation and benchmarks
- `ml/benchmarks/run_benchmark.py` covers ML evaluations.
- Baseline persistence models are used for sea-ice and trajectory benchmarking.
- We do not use a single "Accuracy Percentage" because these are continuous regression problems (distance/concentration errors).

## Part 12 — Testing and debugging
- **Data tests**: `pytest ml/tests/ -v` verifies spatial mapping and strict `merge_asof` temporal isolation.
- **Backend tests**: `PYTHONPATH=. pytest backend/tests/ -v` (Currently 100% passing across 67 tests).
- **Frontend checks**: `cd frontend && npm run check`.
- *Common error*: Missing `ml` module in backend tests -> ensure `PYTHONPATH=.` is set from the root directory.

## Part 13 — Complete execution walkthrough
1. Open the project: `cd offshore`
2. Activate environment: `source .venv/bin/activate`
3. Install backend deps: `pip install -r backend/requirements.txt`
4. Train ML models: `python ml/training/iceberg_xgb_train.py`
5. Run backend tests: `PYTHONPATH=. pytest backend/tests/ -v`
6. Start Backend: `uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`
7. In a new terminal, start Frontend: `cd frontend && npm install && npm run dev`
8. Open the web interface at `http://localhost:3000` (or Vite's port).

## Part 14 — SIH judge preparation
**Q: Is this real Antarctic data?**
A: No, this is high-fidelity synthetic data engineered to demonstrate our pipeline's resilience and mathematical routing algorithms for the SIH 2026 prototype.

**Q: How did you prevent data leakage?**
A: All spatial/temporal alignments use `merge_asof` with backward matching only, strictly preventing the model from seeing future environmental variables.

**Q: What is ML and what is rules?**
A: Iceberg drift and sea-ice concentration are predicted via ML (XGBoost). Route optimization (A*) and alert generation are deterministic rule-based systems built on top of those ML predictions.

## Part 15 — Known limitations and next steps
- **Time-Expanded Routing**: Blocked. Our A* pathfinder cannot evaluate a 5-day route against a forecast that changes dynamically hour-by-hour along that route.
- **Vessel Fuel Analytics**: Blocked. We lack the true hydrodynamic draft/windage equations required to do accurate fuel burns.
- **Real Data**: This system requires integration with live ERA5 or NOAA satellite feeds to become production-ready for real-world Antarctic usage.
