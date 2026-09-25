# FINAL SCIENTIFIC LIMITATIONS
**Project:** SIH 26059 - Antarctic Navigation

## 1. Data Provenance & Synthetic Baselines
- All models (`seaice_xgb_v002`, `iceberg_lstm_v002`) are currently trained and evaluated on **synthetic trajectory/environment data**. No operational field validation has occurred.

## 2. Iceberg Forecast Horizon
- The Iceberg LSTM model is explicitly trained and evaluated for a **T+3h horizon**. Long-duration voyages (e.g., 5-day transits) will quickly exceed the validated coverage. The system does not possess whole-voyage iceberg foresight.

## 3. Risk Aggregation Semantics
- `effective_risk = max(sea_ice_risk, iceberg_risk)` is a **conservative deterministic dominant-hazard aggregation**. It is NOT a combined probability, and multiple hazards do not stack statistically.

## 4. Engineering Assumptions
- **0.5 km Iceberg Radius:** This is a hardcoded engineering assumption for the CPA collision bounding box, not an observed sensor measurement.
- **0.27 km Uncertainty:** This is the Mean Haversine Error from the 4-iceberg held-out test set. It does *not* represent a calibrated P95 empirical envelope or collision probability guarantee.

## 5. Global Routing vs. Regional Graph
- The system successfully calculates paths in local Antarctic subsets (e.g. `[-60, 50] to [-60, 52]`). Trans-oceanic global pathfinding (e.g., Singapore to McMurdo) is likely to encounter graph-connectivity and memory limitations given the 0.5-degree resolution required to capture local hazards.

## 6. Execution Constraints
- Browser UI E2E verification is unverified via automation.
- Production PostgreSQL persistence is currently unverified due to the database being offline; deterministic `DEMO_MODE` is strictly required.
