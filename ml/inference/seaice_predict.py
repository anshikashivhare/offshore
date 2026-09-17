import pandas as pd
import joblib

from ml.path_utils import get_model_path
from ml.training.seaice_train import FEATURE_COLS

_model = None
DEFAULT_MODEL_PATH = get_model_path("seaice_xgb.joblib")


def load_model(path=DEFAULT_MODEL_PATH):
    global _model
    if _model is None:
        _model = joblib.load(path)
    return _model


def predict_concentration(lag_1, lag_2, lag_3, day_of_year, lat, lon):
    """Single-cell forecast. In production this gets called once per grid cell."""
    model = load_model()
    X = pd.DataFrame(
        [
            {
                "lag_1": lag_1,
                "lag_2": lag_2,
                "lag_3": lag_3,
                "day_of_year": day_of_year,
                "lat": lat,
                "lon": lon,
            }
        ]
    )[FEATURE_COLS]
    return float(model.predict(X)[0])


if __name__ == "__main__":
    pred = predict_concentration(
        lag_1=0.4, lag_2=0.42, lag_3=0.38, day_of_year=150, lat=-65.0, lon=-60.0
    )
    print(f"Predicted concentration: {pred:.4f}")
