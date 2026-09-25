# PHASE 18: ICEBERG TRAJECTORY LSTM TRAINING PLAN
**Project:** SIH 26059 - Antarctic Navigation

## 1. Dataset Analysis
- **Dataset:** `iceberg_trajectory_synthetic_2026.csv`
- **Total Rows:** 151,920
- **Unique Icebergs:** 30 (5,064 observations per iceberg)
- **Status:** READY.

## 2. Target Definition
- **Targets:** `target_latitude`, `target_longitude`
- **Physical Meaning:** The future coordinate of the iceberg at `timestamp + forecast_horizon_hours`.

## 3. Feature Structure (Sequence)
The dataset natively provides a temporal window:
- **t-2:** `latitude_t_minus_2`, `longitude_t_minus_2`
- **t-1:** `latitude_t_minus_1`, `longitude_t_minus_1`
- **t:** `latitude_t`, `longitude_t`
- **Environmental Context:** `wind_speed_m_s`, `wind_direction_deg`, `ocean_current_u_m_s`, `ocean_current_v_m_s`, `sea_ice_concentration`

## 4. Train/Validation/Test Split Strategy
**CRITICAL:** Randomly splitting rows will cause massive data leakage because iceberg trajectories are continuous. 
- **Strategy (Spatial/Entity Holdout):** We will split by `iceberg_id`.
  - **Train:** Icebergs 1-21 (70%)
  - **Validation:** Icebergs 22-25 (15%)
  - **Test:** Icebergs 26-30 (15%)
This ensures the model actually learns physics rather than just memorizing a specific iceberg's path.

## 5. Model Architecture (LSTM)
- **Input:** Sequences of length 3 `[t-2, t-1, t]`.
- **Architecture:** 
  - PyTorch LSTM (Hidden size: 64, Layers: 2)
  - Linear Output Layer (Features: 2 for `[target_latitude, target_longitude]`)
- **Hardware:** `mps` (Apple Metal Performance Shaders)

## 6. Evaluation Metrics
- **Haversine Distance (km):** The actual physical distance between the predicted coordinate and the true coordinate.
- **RMSE:** Root Mean Squared Error on raw coordinate outputs.

## 7. Execution Decision
**STATUS: APPROVED FOR TRAINING**
Since the dataset is small (~43 MB) and MPS acceleration is available, training the PyTorch LSTM locally on the M5 chip is completely safe.
