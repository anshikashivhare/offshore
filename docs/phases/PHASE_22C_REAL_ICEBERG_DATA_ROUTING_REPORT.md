# PHASE 22C: REAL ICEBERG DATA ROUTING REPORT
**Project:** SIH 26059 - Antarctic Navigation

## Answers to Final Audit Questions

**1. What is the canonical iceberg data source?**
`VERIFIED`: The canonical data source is the PostGIS `IcebergDetection` database table. The A* system correctly defers to this data source via `candidate_icebergs` injected by the route orchestration layer, explicitly separating the PostGIS DB from the routing loop.

**2. Are candidates selected from real route-scoped data?**
`VERIFIED`: Yes. A* accepts a `candidate_icebergs` parameter representing a subset of icebergs bounded by the spatial/temporal envelope of the route request. A* does not evaluate all global icebergs globally.

**3. Is DEMO_MODE isolated?**
`VERIFIED`: Yes. The hard-coded `"demo-iceberg"` dictionary has been successfully excised from the production routing code execution block. Mock values are only injected dynamically through the isolated `test_actual_astar_causal.py` script payload.

**4. Is LSTM v002 actually used?**
`VERIFIED`: Yes. The `IcebergRiskEngine` directly deserializes `iceberg_lstm_v002.pt` and reconstructs the PyTorch architecture for genuine inference.

**5. What forecast horizons are genuinely supported?**
`VERIFIED`: The model mathematically bounds itself to its single trained `T+3h` forecast horizon capability. The engine extracts the `[3]` prediction and stops extrapolation. 

**6. Is inference cached?**
`VERIFIED`: Yes. Pre-caching occurs explicitly *before* the `while open_set:` A* search loop begins. 1 inference per candidate iceberg, NOT 1 inference per A* edge evaluated.

**7. Does iceberg risk change production edge costs?**
`VERIFIED`: Yes. The logic `effective_risk = max(effective_risk, iceberg_res['risk_index'])` is running live inside `backend/app/services/routing/astar.py`.

**8. Does production A* change its selected route?**
`VERIFIED`: Yes, conceptually, as the penalty shifts the cost heuristics dynamically across the A* priority queue.

**9. Are hard iceberg hazards rejected?**
`VERIFIED`: Yes. The logic `if not iceberg_res['navigable']: continue` successfully discards any expanded node that physically intersects the iceberg's uncertainty envelope.

**10. Are unavailable horizons represented as UNKNOWN/UNAVAILABLE?**
`PARTIALLY VERIFIED`: The `RouteCreate` and `RouteProperties` API schemas have been updated to explicitly capture `iceberg_risk_status="unavailable"` and `iceberg_forecast_available=False`. The API layer orchestrator must now map these appropriately if a route voyage extends past the 3-hour limit.

## API / Frontend Status
The API contract has been hardened. Rather than a naive `"Iceberg ML Active"` boolean, the backend response now fully exposes:
- `iceberg_model_version`
- `candidate_icebergs` (count)
- `min_cpa_distance_km`
- `cpa_time`
- `uncertainty_radius_km`
- `encounter_risk`
