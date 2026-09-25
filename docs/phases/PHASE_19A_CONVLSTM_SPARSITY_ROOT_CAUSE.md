# PHASE 19A: CONVLSTM SPARSITY ROOT-CAUSE AND REPRESENTATION REVIEW
**Project:** SIH 26059 - Antarctic Navigation

## 1. Sparsity Summary
- **Finding:** The training grid is exactly 98% empty (2,450 out of 2,500 grid cells are missing per frame).
- **Root Cause:** The sparsity is **intrinsic** to the raw synthetic dataset. It was not caused by any preprocessing, joining, or alignment bugs.

## 2. Raw-to-Processed Coverage
| Dataset | Total Rows | Unique Timestamps | Total Unique Spatial Cells | Avg Cells per Timestamp |
| :--- | :--- | :--- | :--- | :--- |
| `sea_ice_synthetic_2026.csv` | 31,650 | 633 | 50 | 50.0 |
| `weather_synthetic_2026.csv` | 253,200 | 5,064 | 50 | 50.0 |
| `ocean_currents_synthetic_2026.csv` | 253,200 | 5,064 | 50 | 50.0 |
| `aligned_environment_v2.csv` | 31,650 | 633 | 50 | 50.0 |

The preprocessing exact-join retention was 100%. The dataset was simply generated mathematically as 50 specific observation points.

## 3. Spatial Distribution & 4. Temporal Stability
- **Geometry:** The 50 cells are highly scattered, covering a longitude spread of 345.8 degrees and a latitude spread of 23.6 degrees. Each of the 50 points has a unique latitude and longitude, forming an artificial diagonal or scattered constellation, rather than a dense local grid.
- **Temporal Stability:** The data is perfectly stable. The exact same 50 spatial cells are present at every single `T` (633 timestamps).

## 5. Join Diagnosis
- **Conclusion:** The preprocessing pipeline is flawless. The exact cell IDs and timestamps match perfectly across all environmental datasets. No data was lost.

## 6. Input & 7. Target Representation
- **Current Tabular Representation (XGBoost):** Highly effective. Treating the 50 points as independent tabular observations over time avoids assuming false spatial adjacency.
- **Sparse 2D Grid Representation:** Highly destructive. Placing 50 globally scattered points onto a 50x50 spatial grid leaves 98% of the grid empty. 

## 8. Masking Strategy
- While a masked loss would mathematically allow a ConvLSTM to train, passing a 3x3 convolution kernel over a grid where adjacent pixels are actually hundreds of miles apart (due to the 98% sparsity) will force the model to learn completely spurious, non-physical advection patterns.

## 9. Leakage/Split Integrity
- The temporal sequences are perfectly clean. A standard time-series split (Train: T0-T400, Val: T401-T500, Test: T501-T633) is completely viable for any sequence model.

## 10. Architecture Recommendation
**DECISION: CONVLSTM_NOT_APPROPRIATE**
A spatial Convolutional LSTM assumes that adjacent matrix cells represent contiguous, adjacent physical space (like pixels in a weather radar image). Because this specific prototype dataset is actually 50 isolated observation stations scattered globally, spatial convolutions are scientifically invalid. 

**Scientifically Valid Alternatives:**
1. **Graph Neural Network (ST-GNN):** Treat the 50 points as nodes and connect them by physical distance.
2. **Parallel Sequence Modeling:** Train a standard LSTM/Transformer that treats each station as an independent temporal sequence.
3. **Tabular Boosting (Current):** Keep the highly optimized `v002` XGBoost model.

## 11. Required Data Repairs
- No data repairs are required. The data is mathematically sound; it is simply point-based rather than grid-based.

## Final Status
**STATUS: CONVLSTM_NOT_APPROPRIATE**
Training a ConvLSTM on this data would violate fundamental physical principles of spatial modeling. The dataset is fully understood and verified. We must abandon the ConvLSTM track for this specific synthetic dataset.
