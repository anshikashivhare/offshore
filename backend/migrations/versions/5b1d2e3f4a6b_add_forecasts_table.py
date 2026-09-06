"""Add forecasts table

Revision ID: 5b1d2e3f4a6b
Revises: 273f1c50b9d2
Create Date: 2026-09-03 21:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5b1d2e3f4a6b"
down_revision: Union[str, None] = "5f0d8c2e1a3b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "forecasts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("forecast_horizon_days", sa.Integer(), nullable=False),
        sa.Column("initialization_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("region", sa.JSON(), nullable=False),
        sa.Column("predicted_concentration", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("model_metadata", sa.JSON(), nullable=False),
        sa.Column("quality_flags", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_forecasts_initialization_time"),
        "forecasts",
        ["initialization_time"],
        unique=False,
    )
    op.create_index(
        op.f("ix_forecasts_init_horizon"),
        "forecasts",
        ["initialization_time", "forecast_horizon_days"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_forecasts_init_horizon"), table_name="forecasts")
    op.drop_index(op.f("ix_forecasts_initialization_time"), table_name="forecasts")
    op.drop_table("forecasts")