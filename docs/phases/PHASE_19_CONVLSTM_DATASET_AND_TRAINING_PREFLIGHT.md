# PHASE 19: CONVLSTM DATASET CONSTRUCTION AND TRAINING PREFLIGHT
**Project:** SIH 26059 - Antarctic Navigation

## 1. Dataset Source
- **File:** `ml/data/processed/aligned_environment_v2.csv`
- **Total Rows Analyzed:** 31,650 (synthetic dataset).

## 2. Grid Reconstruction
- **Grid Height (Latitudes):** 50 unique values.
- **Grid Width (Longitudes):** 50 unique values.
- **Spatial Resolution:** Latitude spacing averages 0.48 degrees; Longitude spacing averages 7.05 degrees. 
- **Coordinate Order:** `[longitude, latitude]` for standard GIS mapping.

## 3. Temporal Resolution
- **Unique Timestamps:** 633.
- **Sampling Frequency:** Strictly 24 hours.
- **Temporal Integrity:** There are no missing timestamps in the primary temporal sequence. All records align to a clean 24-hour cadence.

## 4. Missing Cells & Spatial Sparsity (CRITICAL)
- **Finding:** A full 50x50 grid expects 2,500 cells per frame. However, the data contains exactly 50 cells per timestamp.
- **Impact:** 2,450 out of 2,500 cells (98%) in the spatial grid are missing/NaN per frame.
- **Policy:** **Masked Loss**. We must NOT interpolate 98% of the grid, nor should we silently fill it with zero. The ConvLSTM must use a binary spatial mask, calculating loss ONLY on the 50 known cells, allowing the convolutions to operate on zero-padded data without penalizing the model for the padded regions.

## 5. Tensor Contract
- **Shape:** `[batch, time, height, width, channels]`
- **Dimensions:** `[16, 8, 50, 50, 17]`
- **Channels:** 17 approved channels (matching the XGBoost feature contract).

## 6. Target Definition
- **Target:** `sea_ice_concentration` at `T+1` (24-hour lead time).
- **Shape:** `[batch, height, width]` (masked to valid cells).

## 7. Sequence Generation & Split Strategy
- **Sequences:** Sliding window of length $T=8$ days to predict day 9.
- **Chronological Split:** 
  - Train: First 70% of chronological sequences.
  - Validation: Next 15%.
  - Test: Final 15%.
- **Leakage Prevention:** No random shuffling before sequence generation. Windows will not cross the train/validation boundaries.

## 8. Normalization
- Standardization (`mean=0`, `std=1`) will be fitted strictly on the Train set valid cells, then applied to Validation and Test.

## 9. Memory Estimate
- **Total System RAM:** 16 GB (Apple Silicon).
- **Single Batch Size (16):** ~21.76 MB raw tensor footprint.
- **Safety:** The memory footprint is highly manageable. Lazy loading is recommended but not strictly necessary for this prototype volume.

## 10. MPS Smoke Test
- **Backend:** PyTorch 2.8.0 on Apple MPS.
- **Test:** A synthetic 5D tensor successfully passed through 3D/2D convolutions and computed a full forward-backward backward pass without throwing type or device errors.

## 11. Visual Tensor Validation
- The data naturally maps back to a Cartesian grid. Round-trip validation confirmed `original = 0.3368`, `tensor = 0.3368` for exact coordinate extraction.
- An image of the sparse tensor mapping has been generated at `ml/evaluation/convlstm_preflight_sic.png`.

## 12. XGBoost vs ConvLSTM Feature Comparison
- **XGBoost:** Takes 17 pointwise tabular features. Treats every cell independently.
- **ConvLSTM:** Takes the exact same 17 features, but feeds them as a 50x50 spatial map. 
- **Advantage:** ConvLSTM can learn spatial advection (e.g., ice blowing from cell A to cell B), which pointwise XGBoost mathematically cannot see.

## 13. Training Configuration Plan
- **Architecture:** 2-Layer ConvLSTM
- **Sequence Length:** 8
- **Batch Size:** 16
- **Optimizer:** AdamW (1e-3)
- **Loss:** Masked MSE
- **Epochs:** 100 with Early Stopping (patience=10)

## 14. Baseline Strategy
- The model must strictly outperform the `persistence` baseline (RMSE: 0.0206) and the `v002` XGBoost model (RMSE: 0.0165) on the exact same temporal test bounds to earn promotion.

## 15. Artifact Plan
- **Candidate Path:** `ml/models/weights/seaice_convlstm_v001.pt`
- **Metadata Path:** `ml/models/metadata/seaice_convlstm_v001.json`

## Final Status
**STATUS: CONVLSTM_READY_WITH_WARNINGS**
We are cleared for training, but **MUST** implement a masked loss function due to the 98% spatial sparsity of the tabular grid records. Silent zero-padding without a loss mask will destroy the model.
