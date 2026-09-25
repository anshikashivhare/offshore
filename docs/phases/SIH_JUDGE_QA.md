# SIH_JUDGE_QA
**Project:** SIH 26059 - Antarctic Navigation

## 1. Difficult Questions

**"Your data is synthetic. Why should we trust the model?"**
*Answer:* We utilized synthetic simulation data to establish the **computational causality** and architectural validity of our pipeline, because live telemetry from the Southern Ocean is not reliably accessible for this prototype. We proved that if the data is accurate, the pipeline successfully intercepts, interprets, and penalizes the A* graph dynamically. Trust the architecture today; swap the data feed for real Sentinel-1/AIS telemetry tomorrow.

**"Your iceberg forecast is only 3 hours. How is this useful for long Antarctic voyages?"**
*Answer:* The Iceberg LSTM degrades rapidly beyond 3 hours due to the chaotic nature of polar wind and currents. We explicitly constrained the forecast to 3 hours to remain scientifically honest, rather than predicting an inaccurate 5-day path. In operations, this necessitates dynamic, periodic re-routing intervals along the voyage.

**"What exactly does risk=0.4 mean?"**
*Answer:* It is a normalized encounter-risk index driven by our deterministic composite risk engine (`max(sea_ice, iceberg)`). It is *not* a statistical probability of collision, but rather an empirical penalty scalar used to direct the A* routing engine away from concentrated hazards.

**"How do you prevent the AI from hallucinating a route?"**
*Answer:* We built a strict "fail-closed" architecture. If risk data is unavailable (e.g. database goes offline) and the user requests the `Safest` objective, the RouteOrchestrator rejects the route entirely with a 400 Bad Request. We refuse to draw a hallucinatory zero-risk route when data is missing.

**"Why shouldn't we just use Dijkstra?"**
*Answer:* Dijkstra evaluates uniformly in all directions, which is computationally intractable for a global marine grid. We use 4D A* with a time-aware heuristic that aggressively targets the destination while penalizing regions based on dynamic environmental risks.

**"What happens if the model is wrong?"**
*Answer:* We apply a deterministic safety margin. The Iceberg LSTM carries a 0.27 km Mean Haversine Error envelope, and we use a 0.5 km engineering buffer for the closest point of approach. However, this is a decision support system, not an autopilot; the final decision rests with the captain using our validated risk metadata.

## 2. Technical Details

**Why XGBoost for sea ice?**
It efficiently models spatial correlations and non-linear interactions across grid features without the extreme computational overhead of deep learning on large rasters.

**Why LSTM for iceberg trajectory?**
Iceberg kinematics are time-series sequences. LSTMs effectively capture temporal dependencies, momentum, and drift influenced by wind/current sequences over time.

**Why wrapped longitude?**
Subtracting raw longitudes causes mathematically invalid 360° tears at the antimeridian (-180/180). We use modulo-arithmetic `((lon2 - lon1 + 180) % 360) - 180` to safely predict continuous displacement.

**How does iceberg prediction affect A*?**
The LSTM predicts the future position -> We calculate Geodesic CPA between vessel and iceberg -> We derive an encounter risk index -> That index scales the cost of traversing an A* edge.

**Why use max() for risk?**
We use a conservative, dominant-hazard aggregation. Averaging hazards statistically dilutes them—an area with 1.0 Iceberg risk and 0.0 Sea-Ice risk is still deadly; `max()` ensures the A* algorithm treats the edge with maximum severity.
