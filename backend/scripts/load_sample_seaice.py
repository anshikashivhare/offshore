"""
Loads synthetic sea-ice concentration data into the DB so the
/routes/optimize endpoint has real rows to query, instead of the
in-memory synthetic grid.

Replace this with a real NSIDC/Copernicus loader once you have
actual satellite data integrated.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import datetime
import numpy as np
from geoalchemy2.elements import WKTElement

from app.db.database import SessionLocal
from app.db.models import SeaIceObservation


def load_sample_grid(origin_lat=-65.0, origin_lon=-60.0, cell_size_deg=0.1,
                      rows=20, cols=20, date=None):
    date = date or datetime.date.today()
    rng = np.random.default_rng(42)
    grid = rng.uniform(0, 0.6, size=(rows, cols))
    grid[8:12, 5:15] = 0.95  # dense ice band, matches earlier synthetic test

    db = SessionLocal()
    try:
        for r in range(rows):
            for c in range(cols):
                lat = origin_lat - r * cell_size_deg
                lon = origin_lon + c * cell_size_deg
                obs = SeaIceObservation(
                    date=date,
                    lat=lat,
                    lon=lon,
                    concentration=float(grid[r, c]),
                    location=WKTElement(f"POINT({lon} {lat})", srid=4326),
                )
                db.add(obs)
        db.commit()
        print(f"Loaded {rows * cols} sea-ice observations for {date}.")
    finally:
        db.close()


if __name__ == "__main__":
    load_sample_grid()
