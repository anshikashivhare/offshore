# SIH 26059: TECHNICAL DEFENSE PACKAGE
**Antarctic Navigation Decision Support System**

## 1. "Why isn't the system calling the route '100% Safe'?"
**Defense:** Navigation through polar environments cannot be deterministically guaranteed as "100% safe" due to the chaotic kinematics of icebergs, sea-ice drift, and severe weather. Claiming absolute safety is a massive liability. Instead, our system calculates a **Risk-Aware Route** utilizing a deterministic dominant-hazard aggregation method `max(sea_ice, iceberg)`. We surface empirical risk indices and fail closed when risk data is missing (yielding an `INSUFFICIENT_RISK_DATA` error) to protect the vessel, rather than hallucinating a false zero-risk pathway.

## 2. "Your ML models only predict 3 hours into the future. A voyage takes days. How is this useful?"
**Defense:** The Iceberg LSTM (v002) is currently evaluated strictly on a T+3h horizon because kinematic trajectory prediction degrades rapidly beyond that window due to chaotic wind and current drift parameters. The system is designed to dynamically re-evaluate the route at intervals. We explicitly chose to constrain the forecast horizon to 3 hours to remain scientifically honest and mathematically bounded, rather than projecting a 5-day extrapolated path that would possess massive, misleading uncertainty.

## 3. "I see you used 'Synthetic Data' for training. Why should we trust this in the real world?"
**Defense:** Due to the strict unavailability of live, high-resolution telemetry from Southern Ocean icebergs, we utilized synthetic simulation data to establish **computational causality** and **architectural validity**. We have proven that if you supply our A* 4D-Routing Engine with high-fidelity coordinate and environmental data, the pipeline correctly intercepts, interprets, aggregates, and penalizes the routing graph. Moving to production is now purely a matter of swapping the synthetic data feed for real-world Sentinel-1/AIS data streams; the entire mathematical orchestration pipeline requires zero modification.

## 4. "Is your A* heuristic admissible? Can you guarantee the shortest possible path?"
**Defense:** We do not claim admissibility or optimal shortest-path guarantees, because environmental hazards do not adhere to simple Euclidean bounds. Our A* edge-cost formulation is explicitly **monotonic** with respect to increasing normalized risk. We prioritize safe clearance and conservative computational bounds over discovering the theoretical lowest-cost path, which is often computationally intractable in a dynamic 4D maritime grid.

## 5. "What is your 0.27 km Uncertainty value?"
**Defense:** The 0.27 km value is the **Mean Haversine Error (MHE)** calculated explicitly from our held-out 4-iceberg test set. It acts as an empirical error summary of the LSTM's deviation at the T+3h mark. It is NOT a P95 statistical probability confidence interval, and we do not present it as such to the user.

## 6. "What happens if a data provider goes down mid-voyage?"
**Defense:** The architecture dictates a "No-Silent-Zero-Risk" rule. If PostgreSQL fails, or a forecast grid becomes unavailable, the system downgrades the risk metadata to `UNKNOWN` / `UNAVAILABLE`. If the routing objective is set to `Safest`, the backend rejects the request entirely (HTTP 400). It will only route via a `Fastest` fallback if explicitly requested, heavily annotated with array `warnings[]` propagated directly to the React UI.
