# SIH JUDGE QUICK REFERENCE
**Project:** SIH 26059

*10-second defensive answers for rapid-fire questions.*

- **XGBoost:** "Predicts sea-ice spatial concentration grids efficiently."
- **LSTM:** "A 2-layer sequence model capturing wind/current kinematics to predict iceberg drift."
- **CPA:** "Geodesic Closest Point of Approach between vessel trajectory and predicted iceberg."
- **Max Aggregation:** "Returns the dominant risk. Averages would statistically dilute severe isolated hazards."
- **4D A*:** "Optimizes a time-aware heuristic penalty grid based on distance, time, and dynamic environmental risk."
- **Navigability:** "Validates hard vessel limits like draft against bathymetry before passing edges to A*."
- **RouteValidator:** "An independent secondary check on the final GeoJSON to ensure no land crossings or geometry tears."
- **Synthetic Data:** "Used to prove the integration causality pipeline because live Antarctic telemetry is inaccessible for this prototype."
- **Uncertainty:** "0.27km is our Mean Haversine Error on a held-out test set, not a guaranteed collision probability."
- **3h Horizon:** "Trajectory physics degrades rapidly. We bound the LSTM at 3 hours to remain scientifically honest."
- **Failure-Safe:** "If data is missing, we fail closed (HTTP 400). We refuse to draw a zero-risk line blindly."
