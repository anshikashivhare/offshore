import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import IcebergTrack, EnvironmentalData
from ml.trajectory_model.predict import project_trajectory

router = APIRouter(prefix="/iceberg", tags=["iceberg"])


def get_latest_position(db: Session, iceberg_id: str):
    return (
        db.query(IcebergTrack)
        .filter(IcebergTrack.iceberg_id == iceberg_id)
        .order_by(IcebergTrack.timestamp.desc())
        .first()
    )


def get_nearest_environmental_cell(db: Session, lat: float, lon: float, date: datetime.date):
    """
    Fetches all environmental grid points for the date and picks the
    nearest by simple squared distance. Fine for a small grid; for a
    large one, use PostGIS's ST_Distance with a spatial index instead.
    """
    candidates = db.query(EnvironmentalData).filter(EnvironmentalData.date == date).all()
    if not candidates:
        return None
    return min(candidates, key=lambda c: (c.lat - lat) ** 2 + (c.lon - lon) ** 2)


@router.get("/trajectory")
def trajectory(
    iceberg_id: str = Query(..., description="ID of the iceberg to track"),
    num_steps: int = Query(5, description="How many steps ahead to project"),
    db: Session = Depends(get_db),
):
    latest = get_latest_position(db, iceberg_id)
    if latest is None:
        raise HTTPException(status_code=404, detail=f"No tracked position found for iceberg_id={iceberg_id}")

    env = get_nearest_environmental_cell(db, latest.lat, latest.lon, latest.timestamp)
    if env is None:
        raise HTTPException(
            status_code=404,
            detail=f"No environmental data found for date={latest.timestamp}. Load environmental data first.",
        )

    path = project_trajectory(
        latest.lat, latest.lon,
        env.current_u, env.current_v, env.wind_u, env.wind_v,
        num_steps,
    )

    return {
        "iceberg_id": iceberg_id,
        "as_of": latest.timestamp.isoformat(),
        "environmental_source": {"lat": env.lat, "lon": env.lon},
        "projected_path": path,
    }
