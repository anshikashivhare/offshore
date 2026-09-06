"""Extend iceberg detection + trajectory prediction schemas

Revision ID: 7c8d9e0f1a2b
Revises: 5b1d2e3f4a6b
Create Date: 2026-09-03 22:30:00.000000

- Add ``extent`` POLYGON to iceberg_detections
- Add ``forecast_horizon_unit`` and ``predicted_path`` JSON columns to
  iceberg_predictions
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = "7c8d9e0f1a2b"
down_revision: Union[str, None] = "5b1d2e3f4a6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "iceberg_detections",
        sa.Column("extent", geoalchemy2.types.Geometry(geometry_type="POLYGON", srid=4326), nullable=True),
    )
    op.add_column(
        "iceberg_predictions",
        sa.Column("forecast_horizon_unit", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "iceberg_predictions",
        sa.Column("predicted_path", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("iceberg_predictions", "predicted_path")
    op.drop_column("iceberg_predictions", "forecast_horizon_unit")
    op.drop_column("iceberg_detections", "extent")