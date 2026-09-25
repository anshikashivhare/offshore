# PHASE 20: ICEBERG TRAJECTORY DATA AND MODEL PREFLIGHT
**Project:** SIH 26059 - Antarctic Navigation

## 1. Dataset Inventory & Integrity
- **Dataset:** `ml/data/raw/iceberg_trajectory_synthetic_2026.csv`
- **Total Rows:** 151,920
- **Unique Icebergs:** 30
- **Observations per Iceberg:** 5,064 (perfectly uniform).
- **Time Frequency:** Exactly 3 hours. No missing gaps.
- **Status:** **VALID TRAJECTORIES**. The dataset contains highly continuous, long-term trajectories (633 days per iceberg), making it an excellent candidate for sequence modeling.

## 2. Spatial & Physical Integrity
- **Latitude Range:** -75.50 to -57.37
- **Longitude Range:** -179.99 to 179.99
- **Finding:** The icebergs strictly operate in Antarctic waters and directly cross the antimeridian (180°/-180°). 
- **Rule Enforced:** Because of the antimeridian crossing, the ML model **MUST NOT** predict absolute longitude coordinates. An iceberg crossing from 179 to -179 would result in catastrophic gradient explosions if trained on absolute MSE. The model must predict **displacement** (velocity / $\Delta$ lat, $\Delta$ lon).

## 3. Target Definition
- **Input History:** Explicitly pre-lagged in the dataset as `T-2`, `T-1`, `T0` (covering a 9-hour history).
- **Forecast Horizon:** `forecast_horizon_hours` (variable lead times).
- **Target Variable:** The model must predict $\Delta$ (displacement) from `T0` to the target horizon, which will then be mathematically added back to `T0` coordinates (with wrapping) during inference.

## 4. Split Strategy
- **Rule Enforced:** We must use a **Chronological Holdout** or **Iceberg ID Holdout**. Since we have 30 distinct icebergs with long continuous histories, the safest method to prevent spatial-temporal leakage is to hold out 4 specific `iceberg_id`s entirely for the Test set, and 4 for Validation. This guarantees the model generalizes to *unseen* icebergs.

## 5. Model Architecture Review
- **Candidate:** LSTM is scientifically appropriate here because icebergs have momentum and inertia. A sequence model capturing the temporal physics over the 5064-length history is valid.
- **Existing Artifact (`iceberg_lstm_v001.pt`):** The artifact successfully loads as a 2-layer LSTM PyTorch state dictionary. It achieved a 90.79 km Mean Haversine Error in Phase 15.

## 6. Uncertainty Representation
- Point prediction is insufficient for iceberg navigation risk. The LSTM should eventually be adapted to predict a Gaussian distribution (mean and variance) or we must apply a constant historical variance envelope, expanding over the forecast horizon, to feed into the Risk Engine.

## 7. Memory & Training Environment Estimate
- **Hardware:** Apple M5, 16GB RAM, MPS.
- **Memory Footprint:** 150k rows with 15 features is < 50MB in RAM. Training a 2-layer LSTM on this will consume < 1GB of memory. It is fully safe to execute locally on `mps`.

## 8. Training Plan (DO NOT EXECUTE YET)
- **Architecture:** PyTorch LSTM (2 layers, 64 hidden units).
- **Target:** Predict `(target_latitude - latitude_t)` and `(target_longitude - longitude_t)` modulo 360 wrap.
- **Input Features:** Wind vectors (u,v), ocean current vectors (u,v), sea ice concentration, and historical displacements.
- **Loss Function:** MSE on displacement.
- **Metrics:** Mean Haversine Error (km), ADE (Average Displacement Error).
- **Validation:** 4 Held-out Icebergs.

## Final Status
**STATUS: ICEBERG_TRAINING_READY**
The dataset strictly contains real trajectory linkages and is free of temporal gaps. The choice of LSTM is scientifically sound. The critical structural requirement is that the target must be formulated as displacement rather than absolute coordinates to handle the antimeridian.
