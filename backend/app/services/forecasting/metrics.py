import numpy as np


def calculate_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Error"""
    return float(np.mean(np.abs(y_true - y_pred)))


def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Root Mean Square Error"""
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def calculate_spatial_error(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
    """Returns the absolute error array to map spatial distribution of errors."""
    return np.abs(y_true - y_pred)


def calculate_correlation(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Pearson correlation coefficient between truth and prediction."""
    # Flatten arrays for correlation calculation
    yt = y_true.flatten()
    yp = y_pred.flatten()

    if len(yt) < 2:
        return 0.0

    correlation_matrix = np.corrcoef(yt, yp)
    return float(correlation_matrix[0, 1])
