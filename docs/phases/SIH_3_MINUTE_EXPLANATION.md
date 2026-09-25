# SIH 3-MINUTE EXPLANATION
**Project:** SIH 26059

**(0:00 - 0:30) The Problem**
"Navigating the Southern Ocean is highly dangerous. Captains currently rely on static, fragmented datasets to avoid sea-ice and icebergs. The shortest path is rarely the safest path, but dynamically predicting where hazards will drift during a voyage is computationally difficult."

**(0:30 - 1:00) The Solution**
"We built a geospatial decision-support pipeline. It combines live environmental forecasts, machine-learning hazard predictions, vessel-specific constraints, and time-aware path optimization to produce a dynamically risk-aware maritime route."

**(1:00 - 1:45) The Machine Learning Architecture**
"Instead of static avoidance zones, our system anticipates the environment. We use an XGBoost model to evaluate sea-ice concentrations, and a 2-layer LSTM to predict iceberg trajectories based on wind and current drift. Crucially, we use wrapped-longitude math to safely track icebergs across the antimeridian without map-tearing."

**(1:45 - 2:30) The Routing Engine**
"Our predictions feed directly into a 4D A* routing engine. If an iceberg is predicted to drift into the vessel's path, we calculate the geodesic Closest Point of Approach (CPA) and derive an encounter-risk index. We use a conservative `max()` function to combine sea-ice and iceberg risks. The A* algorithm penalizes edges based on this risk, steering the route away from predicted collisions."

**(2:30 - 2:50) The Demo / Fail-Closed**
"Our architecture prioritizes honesty. If you look at our demonstration, you'll see it successfully mapping routes while avoiding landmasses. But more importantly, if critical risk data is unavailable and the user requests the 'Safest' route, our API fails closed. It explicitly throws an error rather than hallucinating a dangerous zero-risk route."

**(2:50 - 3:00) The Limitation**
"Currently, this prototype is evaluated on synthetic training data and the iceberg forecast is validated up to 3 hours. It establishes a complete, computationally sound architecture ready to ingest real-world satellite telemetry."
