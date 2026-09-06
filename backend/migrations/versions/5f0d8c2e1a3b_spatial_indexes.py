"""Add spatial GIST indexes and supporting btree indexes

Revision ID: 5f0d8c2e1a3b
Revises: 273f1c50b9d2
Create Date: 2026-09-03 20:10:00.000000

This migration adds:
- GIST spatial indexes on all geometry columns (PostGIS).
- Additional btree indexes on commonly-filtered temporal and status columns.
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "5f0d8c2e1a3b"
down_revision: Union[str, None] = "273f1c50b9d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SPATIAL_INDEXES = [
    ("ix_routes_geometry_gist", "routes", "geometry"),
    ("ix_risk_cells_geometry_gist", "risk_cells", "geometry"),
    ("ix_alerts_location_gist", "alerts", "location"),
    ("ix_sea_ice_observations_geometry_gist", "sea_ice_observations", "geometry"),
    ("ix_weather_observations_geometry_gist", "weather_observations", "geometry"),
    ("ix_ocean_observations_geometry_gist", "ocean_observations", "geometry"),
    ("ix_icebergs_geometry_gist", "icebergs", "geometry"),
    (
        "ix_iceberg_detections_geometry_gist",
        "iceberg_detections",
        "geometry",
    ),
    (
        "ix_iceberg_trajectory_predictions_predicted_geometry_gist",
        "iceberg_trajectory_predictions",
        "predicted_geometry",
    ),
    (
        "ix_iceberg_trajectory_predictions_uncertainty_gist",
        "iceberg_trajectory_predictions",
        "uncertainty_representation",
    ),
]


BTREE_INDEXES = [
    ("ix_routes_vessel_id", "routes", "vessel_id"),
    ("ix_routes_departure_time", "routes", "departure_time"),
    ("ix_risk_cells_timestamp", "risk_cells", "timestamp"),
    ("ix_alerts_route_id", "alerts", "route_id"),
    ("ix_alerts_timestamp", "alerts", "timestamp"),
    ("ix_alerts_status", "alerts", "status"),
    ("ix_jobs_created_at", "jobs", "created_at"),
]


def upgrade() -> None:
    # PostGIS GIST indexes for geometry columns.
    for name, table, column in SPATIAL_INDEXES:
        try:
            op.execute(
                f"CREATE INDEX IF NOT EXISTS {name} ON {table} USING GIST ({column})"
            )
        except Exception:
            # Table or column may not exist in some partial deployments; skip silently.
            pass

    for name, table, column in BTREE_INDEXES:
        try:
            op.execute(
                f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({column})"
            )
        except Exception:
            pass


def downgrade() -> None:
    for name, _table, _column in reversed(SPATIAL_INDEXES):
        try:
            op.execute(f"DROP INDEX IF EXISTS {name}")
        except Exception:
            pass
    for name, _table, _column in reversed(BTREE_INDEXES):
        try:
            op.execute(f"DROP INDEX IF EXISTS {name}")
        except Exception:
            pass
