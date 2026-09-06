import pytest
import numpy as np
from app.services.forecasting.baseline import BaselinePersistenceForecaster
from app.services.forecasting.metrics import (
    calculate_mae, calculate_rmse, 
    calculate_spatial_error, calculate_correlation
)

@pytest.mark.asyncio
async def test_baseline_persistence_forecaster():
    forecaster = BaselinePersistenceForecaster()
    region = {"min_lon": -10, "min_lat": -10, "max_lon": 10, "max_lat": 10}
    inputs = {"mock": "data"}
    
    assert forecaster.validate_input(inputs) is True
    
    with pytest.raises(ValueError, match="Inputs cannot be empty"):
        forecaster.validate_input(None)
    
    result = await forecaster.predict(inputs, horizon=5, region=region)
    assert result["horizon_days"] == 5
    assert result["predicted_concentration"] == 0.5
    assert result["region"] == region

def test_metrics():
    y_true = np.array([0.0, 0.5, 1.0, 0.8])
    y_pred = np.array([0.1, 0.4, 0.9, 0.8])
    
    mae = calculate_mae(y_true, y_pred)
    assert np.isclose(mae, 0.075)
    
    rmse = calculate_rmse(y_true, y_pred)
    # sqrt(mean([0.01, 0.01, 0.01, 0.0])) = sqrt(0.03 / 4) = sqrt(0.0075) = 0.0866025
    assert np.isclose(rmse, np.sqrt(0.0075))
    
    corr = calculate_correlation(y_true, y_pred)
    assert corr > 0.9  # Should be highly correlated
    
    spatial_err = calculate_spatial_error(y_true, y_pred)
    assert np.allclose(spatial_err, [0.1, 0.1, 0.1, 0.0])
