import numpy as np


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance in kilometers between two points
    on the earth (specified in decimal degrees).
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r


def calculate_trajectory_metrics(y_true, y_pred, lats, lons):
    """
    y_true: [[delta_lat, delta_lon], ...]
    y_pred: [[delta_lat, delta_lon], ...]
    lats: [current_lat, ...]
    lons: [current_lon, ...]
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    lats = np.array(lats)
    lons = np.array(lons)

    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))

    true_next_lats = lats + y_true[:, 0]
    true_next_lons = lons + y_true[:, 1]

    pred_next_lats = lats + y_pred[:, 0]
    pred_next_lons = lons + y_pred[:, 1]

    distances_km = haversine_distance(
        true_next_lats, true_next_lons, pred_next_lats, pred_next_lons
    )

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "mean_position_error_km": float(np.mean(distances_km)),
        "median_position_error_km": float(np.median(distances_km)),
        "p95_position_error_km": float(np.percentile(distances_km, 95)),
    }


def calculate_seaice_metrics(y_true, y_pred):
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))

    return {"mae": float(mae), "rmse": float(rmse)}
