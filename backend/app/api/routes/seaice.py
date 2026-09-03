import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import SeaIceObservation
from ml.seaice_model.predict import predict_concentration

router = APIRouter(prefix="/seaice", tags=["seaice"])


def get_recent_observations(db: Session, lat: float, lon: float, before_date: datetime.date, limit: int = 3):
    """
    Fetches the most recent `limit` observations for a given cell,
    strictly before the target date, ordered newest-first — exactly
    what's needed to build lag_1, lag_2, lag_3.
    """
    return (
        db.query(SeaIceObservation)
        .filter(SeaIceObservation.lat == lat, SeaIceObservation.lon == lon)
        .filter(SeaIceObservation.date < before_date)
        .order_by(SeaIceObservation.date.desc())
        .limit(limit)
        .all()
    )


@router.get("/forecast")
def forecast(
    lat: float = Query(...),
    lon: float = Query(...),
    date: str = Query(..., description="Target forecast date, YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    target_date = datetime.date.fromisoformat(date)
    recent = get_recent_observations(db, lat, lon, target_date)

    if len(recent) < 3:
        raise HTTPException(
            status_code=404,
            detail=f"Not enough historical data for lat={lat}, lon={lon} before {date} "
                   f"(found {len(recent)}, need 3). Load more observations first.",
        )

    lag_1, lag_2, lag_3 = recent[0].concentration, recent[1].concentration, recent[2].concentration
    day_of_year = target_date.timetuple().tm_yday

    prediction = predict_concentration(lag_1, lag_2, lag_3, day_of_year, lat, lon)

    return {
        "lat": lat,
        "lon": lon,
        "date": date,
        "predicted_concentration": round(prediction, 4),
        "based_on_lags": [round(lag_1, 4), round(lag_2, 4), round(lag_3, 4)],
    }
