# SIH DEMO STORYBOARD
**Project:** SIH 26059

## Sequence

**1. Open System & Explain Problem**
- Present the browser rendering `Home.tsx`.
- Explain that standard maritime routing only optimizes for distance. Our system optimizes for distance *and* dynamic hazard avoidance.

**2. Select Origin & Destination**
- Use the map UI to select an Origin (`-60.0, 50.0`) and Destination (`-60.0, 52.0`).

**3. Select Vessel & Objective**
- Select "Research Icebreaker" to establish navigability constraints.
- Choose objective: "Fastest".

**4. Calculate Route**
- Click "Calculate Route". Point out the loading state as the FastAPI orchestrator processes the A* algorithm.

**5. Show Actual Route**
- Once rendered, highlight the GeoJSON LineString avoiding the landmasses and providing distance/duration metrics.

**6. Show Risk Composition**
- Expand the Risk Panel. Emphasize the distinct risk metadata. Point out the `iceberg_lstm_v002` provenance and note that the backend is explicitly recording its ML inference state.

**7. Demonstrate Failure State (Safety First)**
- Change the objective to "Safest" and recalculate.
- *Visual:* The UI displays an inline warning. The API intercepts the request with a `400 Bad Request: INSUFFICIENT_RISK_DATA`.
- *Narrative:* "We are currently in a DEMO mode without a live telemetry database. Because we cannot validate risk, the system refuses to hallucinate a 'Safe' route and protects the vessel by failing closed."

**8. Explain Limitation Honestly**
- Explain that the current prototype proves the causal pipeline using synthetic data, and that iceberg trajectory forecasts are strictly evaluated for a 3-hour horizon.

**9. Return to Clean State**
- Hit the page refresh to prove the state cleanly resets without caching stale, dangerous geometries.
