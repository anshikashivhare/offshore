# EQUATIONS AND UNITS
**Project:** SIH 26059

## 1. Antimeridian Wrapping (Longitude Displacement)
`wrapped_delta_lon = ((lon2 - lon1 + 180) % 360) - 180`
*(Output in decimal degrees, strictly bounded between -180 and 180)*

## 2. Risk Aggregation (Conservative Deterministic)
`composite_risk = max(sea_ice_risk_index, iceberg_risk_index)`

## 3. A* Edge Heuristic Penalty
`cost = (dist_nm * fuel_factor) + (time_hours * beta) + (composite_risk * dist_nm * gamma)`

## 4. Monte Carlo Residual Bootstrap (Phase 33)
`sampled_dlat_i = nominal_predicted_dlat + validation_residual_dlat_i`
`sampled_dlon_i = nominal_predicted_wrapped_dlon + validation_residual_dlon_i`
*(i ∈ [1, 10000])*

## 5. Monte Carlo Empirical Hazard Fraction
`hazard_samples = sum(margin_i <= 0 for all i)`
`hazard_fraction = hazard_samples / n_samples`
*(margin_i evaluates geodesic clearance minus the configurable 0.5km engineering buffer)*
