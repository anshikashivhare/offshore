import joblib
import pandas as pd

from ml.training.trajectory_train import FEATURE_COLS

_model = None


def load_model(path="ml/trajectory_model/trajectory_model.joblib"):
    global _model
    if _model is None:
        _model = joblib.load(path)
    return _model


def predict_next_step(lat, lon, current_u, current_v, wind_u, wind_v):
    model = load_model()
    X = pd.DataFrame([{
        "lat": lat, "lon": lon,
        "current_u": current_u, "current_v": current_v,
        "wind_u": wind_u, "wind_v": wind_v,
    }])[FEATURE_COLS]
    delta_lat, delta_lon = model.predict(X)[0]
    return float(delta_lat), float(delta_lon)


def project_trajectory(lat, lon, current_u, current_v, wind_u, wind_v, num_steps=5):
    """
    Iteratively applies the model's predicted delta to project a
    multi-step trajectory. Environmental features are held constant
    across steps here as a simplification — in a fuller version you'd
    look these up per-step from a forecast/reanalysis grid.
    """
    path = [{"lat": lat, "lon": lon}]
    for _ in range(num_steps):
        delta_lat, delta_lon = predict_next_step(lat, lon, current_u, current_v, wind_u, wind_v)
        lat += delta_lat
        lon += delta_lon
        path.append({"lat": round(lat, 5), "lon": round(lon, 5)})
    return path


if __name__ == "__main__":
    path = project_trajectory(lat=-65.0, lon=-58.0, current_u=0.01, current_v=-0.005,
                                wind_u=0.005, wind_v=0.002, num_steps=5)
    for p in path:
        print(p)
