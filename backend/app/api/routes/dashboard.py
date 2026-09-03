"""
Combines route optimization, sea-ice forecast, and iceberg trajectories
into one call — so the frontend doesn't need to make three separate
requests and stitch the results together itself.
"""

import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.routes.routes import get_ice_grid_from_db
from app.api.routes.seaice import get_recent_observations
from app.api.routes.iceberg import get_latest_position, get_nearest_environmental_cell
from ml.route_optimizer.optimizer import find_route, grid_to_latlon
from ml.seaice_model.predict import predict_concentration
from ml.trajectory_model.predict import project_trajectory

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def dashboard_summary(
    start_row: int = Query(...),
    start_col: int = Query(...),
    end_row: int = Query(...),
    end_col: int = Query(...),
    forecast_lat: float = Query(...),
    forecast_lon: float = Query(...),
    forecast_date: str = Query(..., description="YYYY-MM-DD"),
    iceberg_ids: str = Query("", description="Comma-separated iceberg IDs to include"),
    db: Session = Depends(get_db),
):
    result = {}

    # --- Route ---
    try:
        grid = get_ice_grid_from_db(db)
        route_result = find_route(grid, (start_row, start_col), (end_row, end_col))
        latlon_path = grid_to_latlon(route_result["path"], -65.0, -60.0, 0.1)
        result["route"] = {
            "status": route_result["status"],
            "total_cost": route_result["total_cost"],
            "path": latlon_path,
        }
    except Exception as e:
        result["route"] = {"error": str(e)}

    # --- Sea-ice forecast ---
    try:
        target_date = datetime.date.fromisoformat(forecast_date)
        recent = get_recent_observations(db, forecast_lat, forecast_lon, target_date)
        if len(recent) >= 3:
            lag_1, lag_2, lag_3 = recent[0].concentration, recent[1].concentration, recent[2].concentration
            day_of_year = target_date.timetuple().tm_yday
            pred = predict_concentration(lag_1, lag_2, lag_3, day_of_year, forecast_lat, forecast_lon)
            result["seaice_forecast"] = {"predicted_concentration": round(pred, 4)}
        else:
            result["seaice_forecast"] = {"error": "not enough historical data"}
    except Exception as e:
        result["seaice_forecast"] = {"error": str(e)}

    # --- Iceberg trajectories ---
    trajectories = []
    ids = [i.strip() for i in iceberg_ids.split(",") if i.strip()]
    for iceberg_id in ids:
        try:
            latest = get_latest_position(db, iceberg_id)
            if latest is None:
                trajectories.append({"iceberg_id": iceberg_id, "error": "not found"})
                continue
            env = get_nearest_environmental_cell(db, latest.lat, latest.lon, latest.timestamp)
            if env is None:
                trajectories.append({"iceberg_id": iceberg_id, "error": "no environmental data"})
                continue
            path = project_trajectory(
                latest.lat, latest.lon,
                env.current_u, env.current_v, env.wind_u, env.wind_v,
                5,
            )
            trajectories.append({"iceberg_id": iceberg_id, "projected_path": path})
        except Exception as e:
            trajectories.append({"iceberg_id": iceberg_id, "error": str(e)})
    result["iceberg_trajectories"] = trajectories

    return result
