from datetime import datetime, timezone

import numpy as np
import pytest

from app.schemas.common import GeoJSONFeature
from app.schemas.iceberg import IcebergDetectionProperties
from app.services.icebergs.detection import DeterministicSeededDetector
from app.services.icebergs.trajectory import (
    PhysicsBasedTrajectoryPredictor,
    calculate_ade,
    calculate_fde,
)


class _NoOpSession:
    async def commit(self):
        return None

    async def execute(self, *args, **kwargs):
        raise RuntimeError("not used in this test")


@pytest.mark.asyncio
async def test_iceberg_detection_service():
    detector = DeterministicSeededDetector(_NoOpSession(), n_detections=1)
    spatial_metadata = {
        "min_lon": 10.0, "min_lat": 20.0, "max_lon": 12.0, "max_lat": 22.0,
    }
    timestamp = datetime.now(timezone.utc)

    # Stub the persistence path so we don't need a real DB.
    async def _noop_create(*a, **kw):
        return None
    detector.detect  # ensure attribute exists

    class _FakeRepo:
        async def get_or_create(self, *a, **kw):
            from app.models.iceberg import Iceberg
            return Iceberg(iceberg_id=kw["iceberg_id"])

        async def create(self, *a, **kw):
            return None

    import app.services.icebergs.detection as det_mod
    det_mod.iceberg_repo = _FakeRepo()
    det_mod.detection_repo = _FakeRepo()

    detections = await detector.detect("mock_ref", timestamp, spatial_metadata)
    assert len(detections) == 1
    det = detections[0]
    assert det.type == "Feature"
    assert det.geometry.type == "Point"
    assert 0.5 <= det.properties.confidence <= 0.99
    # Coordinates are inside the requested bbox.
    assert 10.0 <= det.geometry.coordinates[0] <= 12.0


@pytest.mark.asyncio
async def test_iceberg_trajectory_predictor():
    predictor = PhysicsBasedTrajectoryPredictor(_NoOpSession())

    class _FakePredictionRepo:
        async def create(self, *a, **kw):
            return None

    import app.services.icebergs.trajectory as traj_mod
    traj_mod.prediction_repo = _FakePredictionRepo()

    iceberg_id = "11111111-1111-1111-1111-111111111111"
    predictions = await predictor.predict_trajectory(
        iceberg_id=iceberg_id,
        historical_track=[],
        environmental_conditions={
            "current_speed_mps": 0.5,
            "current_direction_deg": 90.0,
            "wind_speed_mps": 5.0,
            "wind_direction_deg": 0.0,
        },
        horizon_hours=5,
        start_time=datetime.now(timezone.utc),
    )

    assert len(predictions) == 5
    # Uncertainty is now a WKT POLYGON string, not a "radius_" token.
    assert predictions[-1].properties.uncertainty_representation.startswith("POLYGON(")


def test_trajectory_metrics():
    y_true = np.array([[0, 0], [1, 1], [2, 2]])
    y_pred = np.array([[0, 0.1], [1, 1.1], [2, 2.1]])
    ade = calculate_ade(y_true, y_pred)
    assert np.isclose(ade, 0.1)
    fde = calculate_fde(y_true, y_pred)
    assert np.isclose(fde, 0.1)