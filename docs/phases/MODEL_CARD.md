# MODEL CARD
**Project:** SIH 26059

## Sea-Ice XGBoost
- **Version:** v002
- **Training Data:** Synthetic grids

## Iceberg LSTM
- **Version:** v002
- **Architecture:** 2-layer LSTM
- **Validation Split:** 4 icebergs
- **Test Split:** 4 icebergs
- **Horizon:** T+3h

### Uncertainty Methodology (Phase 33)
- **Method:** Empirical residual bootstrap (Monte Carlo)
- **Calibration Split:** Validation
- **Sample Count:** 10,000 (configurable)
- **Mechanism:** Residuals from the validation predictions are sampled and added to the nominal prediction to form an empirical separation envelope during routing. 
- **Limitation:** Uncertainty is derived from synthetic data residuals. It is an empirical propagation of forecast variance, not a calibrated collision probability.
