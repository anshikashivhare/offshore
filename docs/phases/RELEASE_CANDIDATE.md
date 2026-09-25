# RELEASE CANDIDATE: SIH-26059-RC1

**Date:** 2026-09-25
**Scope:** Risk-Aware Antarctic Navigation Decision-Support Prototype

## Major Components
- **Sea-Ice Forecast ML:** XGBoost (v002)
- **Iceberg Trajectory ML:** LSTM (v002) with Empirical Residual Monte Carlo Bootstrap
- **Pathfinder:** 4D Time-Aware A* with Composite Risk Heuristics
- **API:** FastAPI Orchestrator
- **Frontend:** React + Mapbox GL

## Known Limitations (Environment-Blocked)
- **PostGIS Production Workflow:** Unverified locally due to container `sudo` restrictions. Application must run in `DEMO_MODE=True`.
- **Automated Browser E2E:** Unverified locally due to Playwright constraints.

## Known Limitations (Scientific)
1. **Synthetic Data:** The system was trained and evaluated on synthetic trajectory grids. It lacks real-world Sentinel-1/AIS operational calibration.
2. **Horizon Constraint:** Iceberg forecasting is strictly bounded to T+3h. Extrapolation is blocked.
3. **Probability Claims:** Monte Carlo outputs represent an *empirical simulated hazard fraction* derived from validation errors, **not** a calibrated collision probability.
4. **Resolution Limits:** A* path sampling resolution limits detection of sub-grid spatial anomalies on extremely long edges.
5. **Certification:** This is a decision-support prototype. It is NOT operationally safe or navigation-certified.

## Startup Procedure
```bash
./scripts/start_demo.sh
```
