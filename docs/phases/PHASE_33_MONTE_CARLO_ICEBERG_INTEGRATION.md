# PHASE 33: MONTE CARLO ICEBERG INTEGRATION
**Project:** SIH 26059

## 1. Objective
Integrated Monte Carlo uncertainty propagation into the existing Iceberg LSTM v002 → CPA → Risk → A* pipeline. This provides an empirical distribution of separation distances to derive risk, rather than relying on a deterministic scalar margin.

## 2. Architecture
The `MonteCarloIcebergSimulator` component was integrated directly into `IcebergRiskEngine`.
- **Pre-A* Expansion:** When `predict_iceberg_trajectory` is called, the nominal displacement is calculated, and `n_samples` (default: 10,000) are generated via empirical residual bootstrap. The samples are cached directly within the iceberg context.
- **A* Edge Evaluation:** The A* loop (`evaluate_edge_risk`) queries the cached MC samples. It calculates geodesic distances against all 10,000 samples, computing the `hazard_fraction` and `p05_margin`.
- **No Per-Edge Explosion:** Monte Carlo is explicitly generated *once* per iceberg per route request, avoiding catastrophic N-squared looping inside A*.

## 3. Uncertainty Source & Calibration
- The MC samples are drawn from validation residuals (`val_residuals_dlat`, `val_residuals_dlon`) isolated from the LSTM v002 validation split.
- **Leakage Audit:** Test residuals were explicitly forbidden from entering the sampling distribution.

## 4. Antimeridian Safety
Longitude sampling explicitly uses modulo arithmetic to prevent 360° tearing:
`normalize_longitude(iceberg_state['lon'] + d)`

## 5. CPA Distribution & Risk Mapping
The empirical hazard fraction is derived from sample encounters:
- `hazard_fraction > 0.05` → CRITICAL (Risk = 1.0, Navigable = False)
- `hazard_fraction > 0` or `warning_fraction > 0.1` → WARNING (Risk = 0.5)

## 6. Limitations
- **Data Provenance:** The residual calibration is derived from synthetic validation data.
- **Probability Claims:** The hazard fraction represents simulated encounters, NOT a calibrated real-world collision probability.
- **Horizon:** Extrapolation beyond T+3h remains explicitly UNAVAILABLE.
