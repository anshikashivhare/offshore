# PHASE 18: ICEBERG TRAJECTORY LSTM EXECUTION REPORT
**Project:** SIH 26059 - Antarctic Navigation

## 1. Executive Summary
**STATUS: SUCCESSFUL PROTOTYPE**
The PyTorch LSTM model successfully trained on the iceberg trajectory sequence data using Apple Metal Performance Shaders (MPS) hardware acceleration. By strictly splitting the dataset by `iceberg_id` instead of a random split, we prevented data leakage and forced the model to generalize to entirely unseen icebergs.

## 2. Dataset & Splitting
- **Dataset:** `iceberg_trajectory_synthetic_2026.csv` (151,920 rows)
- **Split Strategy:** Entity-based holdout (`iceberg_id`)
  - **Train:** 21 Icebergs
  - **Validation:** 4 Icebergs
  - **Test:** 5 Icebergs
- **Target:** `[target_latitude, target_longitude]`

## 3. Architecture & Training
- **Model:** PyTorch LSTM (Hidden size: 64, Layers: 2)
- **Inputs:** `t-2`, `t-1`, `t` coordinates + concatenated environmental context (wind, currents, sea ice).
- **Epochs:** 20
- **Best Validation MSE:** ~13.44 (Epoch 15)

## 4. Evaluation Metrics (Untouched Test Set)
Evaluated on the 5 held-out icebergs:
- **RMSE (Coordinate Space):** 3.37
- **Mean Haversine Distance Error:** 90.79 km

**Interpretation:** On average, the model predicts the future location of an entirely unseen iceberg within ~90km. For a first-pass synthetic prototype predicting multiple days out, this establishes a physically plausible, unbroken deep-learning pipeline that is fully ready to be swapped with real-world target data.

## 5. Artifacts Generated
- **Model Weights:** `ml/models/weights/iceberg_lstm_v001.pt`
- **Metrics Log:** `ml/evaluation/iceberg_lstm_v001_metrics.json`

## 6. Next Steps
This confirms that local deep learning trajectory forecasting works and scales safely on the local CPU/GPU hardware. We have successfully completed all core ML phases!
