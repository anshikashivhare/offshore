"""
Loads synthetic ocean current + wind data so the iceberg trajectory
endpoint has something to look up. Replace with a real ERA5/Copernicus
loader later — same pattern as load_sample_seaice.py.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import datetime
import numpy as np
from geoalchemy2.elements import WKTElement

from app.db.database import SessionLocal
from app.db.models import EnvironmentalData


def load_sample_grid(origin_lat=-65.0, origin_lon=-60.0, cell_size_deg=0.1,
                      rows=20, cols=20, date=None):
    date = date or datetime.date.today()
    rng = np.random.default_rng(7)

    db = SessionLocal()
    try:
        for r in range(rows):
            for c in range(cols):
                lat = origin_lat - r * cell_size_deg
                lon = origin_lon + c * cell_size_deg
                env = EnvironmentalData(
                    date=date,
                    lat=lat,
                    lon=lon,
                    current_u=float(rng.uniform(-0.02, 0.02)),
                    current_v=float(rng.uniform(-0.01, 0.01)),
                    wind_u=float(rng.uniform(-0.01, 0.01)),
                    wind_v=float(rng.uniform(-0.005, 0.005)),
                    location=WKTElement(f"POINT({lon} {lat})", srid=4326),
                )
                db.add(env)
        db.commit()
        print(f"Loaded {rows * cols} environmental grid points for {date}.")
    finally:
        db.close()


if __name__ == "__main__":
    load_sample_grid()
