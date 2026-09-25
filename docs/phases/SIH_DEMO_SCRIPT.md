# SIH DEMO SCRIPT
**Project:** SIH 26059 - Antarctic Navigation

## Sequence

**00:00 - Launch**
Execute `./scripts/start_demo.sh`. Point browser to `http://localhost:5173`. Acknowledge that the system is operating in DEMO_MODE explicitly.

**00:30 - Establish Origin**
Select `-60.0, 50.0`. Point out the origin marker rendered via GeoJSON.

**00:45 - Establish Destination**
Select `-60.0, 52.0`. Point out the destination marker.

**01:00 - Select Vessel**
Select the `Research Icebreaker` (PC1). Note that vessel metadata determines navigability constraints internally.

**01:15 - Select Objective (Fastest)**
Choose the `Fastest` heuristic objective to allow graceful degradation of risk models.

**01:30 - Execute Route**
Click "Calculate Route". Point out the UI Loading states and wait for the `GeoJSON Feature` response from FastAPI.

**02:00 - Inspect Route**
Hover over the rendered LineString. Show that it avoids the landmass and has successfully calculated distance in NM and duration.

**02:30 - Inspect Risk Fallbacks**
Click to the "Safest" objective and re-calculate. The UI should instantly catch a 400 Error (Insufficient Risk Data) and refuse to plot a 0-risk line, proving the system's safety-critical fail-closed architecture.

**03:00 - Inspect Model Provenance**
Expand the details/warnings panel. Point out the exact version strings (e.g. `iceberg_lstm_v002`) proving ML inference was mapped.

**03:30 - Explain Synthetic Data Constraint**
Verbally disclose: "The ML models displayed here are currently driven by synthetic trajectory training data and are operating in a deterministic demo mode. They establish computational causality, not real-world certification."
