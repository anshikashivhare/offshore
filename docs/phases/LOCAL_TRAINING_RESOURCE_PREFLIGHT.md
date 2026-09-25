# LOCAL TRAINING RESOURCE PREFLIGHT
**Project:** SIH 26059 - Antarctic Navigation
**Phase:** Local Resource Preflight

## 1. Machine
- **CPU Architecture:** `arm64`
- **macOS Version:** `26.6.2`
- **Python Version:** `3.9.6`
- **Virtual Environment:** Active (`.venv`)
- **CPU Model:** Apple M5
- **Logical Cores:** 10
- **Total RAM:** 16.0 GB
- **Available RAM:** 4.15 GB
- **Free Disk Space:** 348.23 GB

## 2. Runtime
- **XGBoost:** v2.1.4
- **PyTorch:** v2.8.0

## 3. XGBoost Capability
- Fully supported and imported successfully.
- Will default to utilizing multiple logical cores via OpenMP.

## 4. PyTorch Capability
- Fully supported and imported successfully.

## 5. MPS Capability
- **MPS Built:** `True`
- **MPS Available:** `True`
- *Conclusion:* Hardware acceleration (Apple Silicon GPU) is fully available for PyTorch.

## 6. Dataset Inventory
| Filename | Size (MB) | Rows | Est. RAM (MB) | Synthetic |
|----------|----------|------|---------------|-----------|
| `ocean_currents_synthetic_2026.csv` | 41.09 | 253,200 | 87.96 | Yes |
| `routes_synthetic_2026.csv` | 0.01 | 30 | 0.01 | Yes |
| `iceberg_trajectory_synthetic_2026.csv` | 43.40 | 151,920 | 67.41 | Yes |
| `weather_synthetic_2026.csv` | 62.26 | 253,200 | 99.55 | Yes |
| `grid_cells_2026.csv` | 0.00 | 50 | 0.00 | Yes |
| `sea_ice_synthetic_2026.csv` | 6.07 | 31,650 | 11.69 | Yes |
| `route_waypoints_synthetic_2026.csv` | 0.19 | 1,401 | 0.43 | Yes |

*Total Estimated RAM for all datasets combined is < 300 MB.*

## 7. Memory Estimates
- **XGBoost sea-ice:** ~12MB data RAM + ~50MB overhead -> Peak ~100MB
- **LSTM trajectory:** ~67MB data RAM + PyTorch tensor/MPS overhead -> Peak ~400MB
- **ConvLSTM sea-ice (if applicable):** ~100MB data RAM + model weights -> Peak ~600MB
- **Available RAM:** 4,154 MB.
- *Status:* We are well within safe memory limits.

## 8. Model-by-Model Feasibility
- **XGBoost sea-ice:** **SAFE_LOCAL**
- **LSTM trajectory:** **SAFE_LOCAL**
- **ConvLSTM sea-ice:** **SAFE_LOCAL**

## 9. Crash Risks
- Datasets are small enough that chunking is technically not required, but good practice.
- The only risk is PyTorch MPS memory leaking if tensors are not detached correctly in loops. Memory cleanup after epochs is recommended.
- Current free RAM (4.15 GB) is adequate but background apps might fluctuate it.

## 10. Colab vs Local Comparison
| Model | Dataset Size | Est. RAM | Est. Train Time | Local CPU | Local MPS | Colab GPU | Recommended |
|-------|-------------|----------|-----------------|-----------|-----------|-----------|-------------|
| XGBoost (Sea Ice) | 6.1 MB | 100 MB | < 2 mins | Excellent | N/A | Excellent | **Local CPU** |
| LSTM (Iceberg) | 43.4 MB | 400 MB | ~10 mins | Good | Excellent | Excellent | **Local MPS** |

## 11. Recommended Training Environment
Because the Colab MCP proxy is offline (due to the broken Playwright driver) and the synthetic datasets are exceptionally small and manageable, **Local Training (Mac M5)** is heavily recommended. PyTorch can leverage the `mps` backend for fast deep learning training.

## 12. Pre-Training Checklist
- [x] Verified dataset sizes and RAM estimates.
- [x] Verified XGBoost and PyTorch imports.
- [x] Verified Apple MPS availability.
- [ ] Implement checkpoint saving logic for new artifacts (e.g. `seaice_xgb_v002.json`).
- [ ] Explicitly avoid overwriting `seaice_xgb_latest.json`.
