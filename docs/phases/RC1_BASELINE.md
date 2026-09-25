# RC1 BASELINE
**Project:** SIH 26059

## Architecture Overview
The RC1 baseline provides a feature-complete decision-support prototype. It orchestrates user requests from a React frontend through a FastAPI backend, executing a 4D Time-Aware A* pathfinder.

### Models
- **Sea-Ice Forecast ML:** XGBoost v002 (Predicts gridded sea-ice concentration/risk)
- **Iceberg Trajectory ML:** LSTM v002 (Predicts coordinate displacement up to T+3h horizon)

### Risk Formulation
- **Iceberg Risk:** Empirical residual bootstrap (Monte Carlo) draws 10,000 samples to compute an empirical hazard fraction.
- **Composite Risk:** `max(sea_ice_risk, iceberg_risk)`

### Routing
- **4D Time-Aware A*:** Nodes encode `(lat, lon, time)`. Heuristic cost evaluates dynamic hazard exposure at the estimated arrival time. 
- **RouteValidator:** Mirrors A* risk logic to compute the final geometry safety, CPA, and margin values.

### Known Environment Blockers
- **PostGIS Production Path:** Missing local container `sudo` execution prevents PostgreSQL installation. The application relies entirely on `DEMO_MODE=True` for data provision.
- **Browser Automation:** Missing local Playwright dependencies prevents E2E CI/CD execution.
