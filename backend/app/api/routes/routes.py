import sys
import os
import numpy as np
from fastapi import APIRouter, HTTPException

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from ml.route_optimizer.optimizer import find_route, grid_to_latlon
from app.models.route_schemas import RouteRequest, RouteResponse, RoutePoint

router = APIRouter(prefix="/routes", tags=["routes"])


from sqlalchemy.orm import Session
from fastapi import Depends
from app.db.database import get_db
from app.db.models import SeaIceObservation
import datetime

def get_ice_grid_from_db(db: Session, date=None, rows=20, cols=20,
                          origin_lat=-65.0, origin_lon=-60.0, cell_size_deg=0.1) -> np.ndarray:
    date = date or datetime.date.today()
    observations = db.query(SeaIceObservation).filter(SeaIceObservation.date == date).all()

    grid = np.zeros((rows, cols))
    for obs in observations:
        r = round((origin_lat - obs.lat) / cell_size_deg)
        c = round((obs.lon - origin_lon) / cell_size_deg)
        if 0 <= r < rows and 0 <= c < cols:
            grid[r, c] = obs.concentration
    return grid

@router.post("/optimize", response_model=RouteResponse)
def optimize_route(req: RouteRequest, db: Session = Depends(get_db)):
    grid = get_ice_grid_from_db(db)
    rows, cols = grid.shape

    for name, val, limit in [("start_row", req.start_row, rows),
                              ("start_col", req.start_col, cols),
                              ("end_row", req.end_row, rows),
                              ("end_col", req.end_col, cols)]:
        if not (0 <= val < limit):
            raise HTTPException(status_code=400, detail=f"{name}={val} is out of grid bounds")

    result = find_route(
        grid,
        start=(req.start_row, req.start_col),
        end=(req.end_row, req.end_col),
    )

    latlon_path = grid_to_latlon(
        result["path"], req.origin_lat, req.origin_lon, req.cell_size_deg
    )

    return RouteResponse(
        status=result["status"],
        total_cost=result["total_cost"],
        path=[RoutePoint(**p) for p in latlon_path],
        reason=result.get("reason"),
    )
