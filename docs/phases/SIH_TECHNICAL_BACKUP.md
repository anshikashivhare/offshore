# SIH TECHNICAL BACKUP
**Project:** SIH 26059

*Use these detailed specs if judges ask for mathematical or architectural proof.*

## 1. Iceberg LSTM Antimeridian Mathematics
To prevent the model from failing when an iceberg crosses the 180° / -180° boundary, we do not predict raw longitude. Instead, we predict the displacement (`delta_lon`) wrapped via modulo arithmetic:
`wrapped_delta_lon = ((lon2 - lon1 + 180) % 360) - 180`
This preserves spatial continuity for the LSTM across the globe.

## 2. Risk Aggregation
We use a conservative, deterministic scalar for risk:
`effective_risk = max(sea_ice_risk, iceberg_risk_index)`
This ensures that the routing engine does not dilute a critical iceberg threat simply because sea-ice levels happen to be low in the same grid cell.

## 3. Data Split Evidence
The Iceberg LSTM (v002) was trained strictly on an isolated subset:
- **Train:** 22 Icebergs
- **Validation:** 4 Icebergs
- **Test:** 4 Icebergs
The reported `0.27 km` MHE is derived exclusively from the 4 held-out test icebergs.

## 4. 4D A* Edge Cost Evaluation
A* evaluates paths based on distance, time, and dynamic environmental penalties:
`cost = (dist_nm * fuel_factor) + (time_hours * beta) + (effective_risk * dist_nm * gamma)`
The environmental risk penalty (`gamma`) scales monotonically, ensuring hazardous edges are deprioritized without claiming absolute global mathematical shortest-path optimality.
