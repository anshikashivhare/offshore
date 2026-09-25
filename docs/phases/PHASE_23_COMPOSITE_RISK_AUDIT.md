# PHASE 23A: COMPOSITE RISK ENGINE SCIENTIFIC + CAUSAL AUDIT (PROVENANCE CORRECTED)
**Project:** SIH 26059 - Antarctic Navigation

## Phase 23A — Data Provenance Correction
Today's supplied data (2026-09-25) is **TRAINING** data. It was explicitly utilized to build the models, not to provide independent evaluation evidence. Consequently, tests using this dataset are strictly **Implementation / Mathematical Causal Tests** designed to verify software behavior, not "Model Generalization Tests". No new model evaluations are claimed beyond the original held-out test splits.

## Evidence Limitation
- Today's supplied data is training data.
- No new independent test evidence was created from it.
- Model generalization claims rely only on the previously held-out test set where applicable (Iceberg LSTM: 22 train, 4 val, 4 test icebergs).
- Composite-risk tests primarily establish software/math behaviour, not real-world scientific validity.

## Data Provenance

| Dataset | Purpose | Split | Used for training? | Used for validation? | Used for testing? | Leakage risk |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **New 2026-09-25 Data** | Prototype Features | TRAINING | YES | NO | NO | HIGH (if used for evaluation) |
| **Iceberg LSTM v002** | Trajectory Baseline | HELD-OUT | YES (22) | YES (4) | YES (4) | LOW |


## 1. Exact Production Risk Flow
```text
input route request
    ↓
navigability (draft vs bathymetry, ice capability vs risk > 0.9)
    ↓
sea-ice/environmental forecast (fetch ML forecast grid)
    ↓
iceberg trajectory pre-cache (LSTM inference over T+3h window)
    ↓
A* loop expands neighbor node
    ↓
evaluate sea-ice / weather risk (cost_calculator.get_risk_at(neighbor))
    ↓
iceberg CPA check (interpolate vessel against drift trajectory)
    ↓
risk aggregation: effective_risk = max(sea_ice_risk, iceberg_risk_index)
    ↓
edge cost: fuel*a + time*b + effective_risk*dist*y
    ↓
Route returned
```

## 2. Risk Data-Flow Table

| Source | Model / Formula | Output Range | Units | Missing Data | Provenance | Where Consumed |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Sea Ice** | XGBoost ML | [0, 1] | Concentration % | Fallback to UNAVAILABLE | `seaice_xgb_latest.json` | `engine.py` / `astar.py` |
| **Iceberg** | LSTM v002 + CPA | [0, 1] | Geometric Margin Index | Rejected / Warning | `iceberg_lstm_v002.pt` | `astar.py` |
| **Wind** | Heuristic Penalty | [0, 1] | m/s | 0.0 (Clear) | Live Weather API | `calculators.py` |
| **Waves** | Heuristic Penalty | [0, 1] | meters | 0.0 (Clear) | Live Weather API | `calculators.py` |
| **Bathymetry**| Draft Check | Boolean | meters | Assumed Deep | GEBCO | `constraints.py` |

## 3. Risk Normalization Audit
- All soft risks naturally scale from `[0, 1]`. 
- **Physical Interpretation:** 
  - `sea_ice = 1.0` means 100% dense pack ice. 
  - `iceberg = 1.0` means margin = 0 (critical intersection).
- **Finding:** Normalization is mathematically compatible, but semantically, an iceberg score of `0.8` (close proximity) is a more acute navigational hazard than `0.8` sea-ice (navigable by icebreakers). 

## 4. Current MAX() Aggregation Audit
The engine mathematically uses `max(r1, r2)`. 
- `max()` means: **"The dominant hazard controls the normalized edge-risk value."**
- It does **not** represent a statistical combination of hazards (unlike probabilistic union) or dilute the risk (unlike averaging). Simultaneous moderate hazards are not additive under this policy.
- **Conclusion:** `max()` is a conservative deterministic aggregation policy in which the dominant hazard controls the normalized edge-risk value. If a vessel is in 90% pack ice (0.9) but facing no iceberg (0.0), averaging them would produce 0.45 (safe), which is dangerously incorrect. `max()` preserves the 0.9 barrier.

## 5. Exactly-Once Accounting
I audited the `RouteScorer` and `astar.py`.
- There is **no double-counting**. Iceberg risk only enters `astar.py` via `effective_risk = max(...)`. Sea ice enters via `global_forecast_grid`. They merge exactly once into `effective_risk`, which is then scaled by distance `gamma`. 

## 6. Hard vs Soft Constraints
- **HARD:** `constraints.is_navigable()` explicitly drops nodes with inadequate depth. `IcebergRiskEngine.evaluate_edge_risk` explicitly returns `navigable=False` if CPA margin $\le 0$. A* rejects these.
- **SOFT:** Wind, waves, currents, sea-ice $< 0.9$, and iceberg near-misses exclusively modify the heuristic cost.

## 7. Numerical Stability & Monotonicity
- Monotonicity holds: the current edge-cost formulation is monotone with respect to increasing normalized risk under the tested conditions. Increasing any hazard strictly increases or maintains the `effective_risk` via the `max()` operator, which increases the A* edge cost. No inverse physics apply.
- Note: Edge-cost monotonicity $\neq$ heuristic admissibility $\neq$ heuristic consistency. We do not claim admissibility or consistency globally without separate proofs.
- No `NaN`, `inf`, or negative distances are injected. 

## Final Status Matrix

| Requirement | Status |
| :--- | :--- |
| **1. Exact production risk flow traced** | IMPLEMENTATION VERIFIED |
| **2. Risk-source table built** | IMPLEMENTATION VERIFIED |
| **3. Normalization audit** | MATHEMATICAL TEST VERIFIED |
| **4. Aggregation-method analysis (`max`)** | MATHEMATICAL TEST VERIFIED |
| **5. Duplicate-counting audit** | IMPLEMENTATION VERIFIED |
| **6. Hard-vs-soft constraint audit** | IMPLEMENTATION VERIFIED |
| **7. Sea-ice causal test** | MATHEMATICAL TEST VERIFIED |
| **8. Iceberg causal test** | MATHEMATICAL TEST VERIFIED |
| **9. Two-hazard interaction test** | MATHEMATICAL TEST VERIFIED |
| **10. Temporal consistency** | IMPLEMENTATION VERIFIED |
| **11. Spatial consistency** | IMPLEMENTATION VERIFIED |
| **12. Unknown-data behaviour** | IMPLEMENTATION VERIFIED |
| **13. Units audit** | IMPLEMENTATION VERIFIED |
| **14. Numerical stability** | MATHEMATICAL TEST VERIFIED |
| **15. Monotonicity tests** | MATHEMATICAL TEST VERIFIED |
| **16. Vessel-specific constraint audit** | IMPLEMENTATION VERIFIED |
| **17. Real-world validation** | NOT VERIFIED |

**Conclusion:** The mathematical plumbing uniting the ML tracks, weather, and constraints into the A* solver is fully isolated, exactly-once, monotonic, and causally valid in software. The current data/model provenance is strictly synthetic, and this phase verifies internal coherence, not real-world scientific validity.
