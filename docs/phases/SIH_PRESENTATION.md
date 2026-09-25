# SIH 26059: PRESENTATION OUTLINE
**Antarctic Navigation Decision Support System**

## Slide 1: The Problem
- **Challenge:** Maritime routing in the Southern Ocean relies on static, disconnected, and often stale datasets.
- **Danger:** Captains lack integrated, 4D spatial awareness of dynamic hazards (drift ice, rapidly shifting weather, and icebergs).
- **Goal:** A Decision Support System that dynamically aggregates environmental models into a spatial pathfinding graph.

## Slide 2: The Solution (Our Architecture)
- **Data Integration:** Fuses live Weather/Marine APIs, Sea-Ice forecasts (XGBoost), and Iceberg Kinematics (LSTM).
- **Routing Engine:** Time-Aware 4D A* Algorithm operating over a high-resolution hex/grid mesh.
- **Safety First:** A strict "Fail-Closed" backend that rejects routing if critical hazard data is unavailable.

## Slide 3: Live Demonstration (The Happy Path)
*Operator executes `SIH_DEMO_SCRIPT.md`*
- Show the React Interface.
- Select Vessel (Research Icebreaker).
- Select Objective (Fastest).
- Generate Route -> Show GeoJSON LineString avoiding landmasses.
- Highlight the **Risk Metadata Panel**, displaying actual model provenance (e.g. `LSTM v002`) and empirical uncertainty.

## Slide 4: Live Demonstration (The Safety Catch)
*Operator alters objective to "Safest"*
- Show how the API instantly intercepts the request and issues a `400 Bad Request`.
- Explain: "Because we are in a demo environment without live DB telemetry, the system refuses to draw a '0-risk' line. It knows data is missing and protects the vessel. No hallucinations."

## Slide 5: Scientific Integrity & Machine Learning
- **XGBoost Sea-Ice:** Predicts spatial concentration.
- **LSTM Iceberg Trajectory:** Predicts T+3h drift utilizing wrapped-longitude math to avoid antimeridian map-tearing.
- **Composite Risk:** Uses `max(sea_ice, iceberg)` to ensure the dominant physical hazard dictates the route penalty, avoiding dangerous statistical dilution.

## Slide 6: Future Roadmap (Bridging to Production)
- **Data Upgrades:** Swap synthetic training weights for operational Sentinel-1 SAR and AIS telemetry.
- **Horizon Expansion:** Advance the LSTM horizon beyond T+3h utilizing probabilistic ensembles.
- **Global Mesh:** Deploy PostGIS routing topologies for seamless trans-oceanic navigation.
