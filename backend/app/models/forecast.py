from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Forecast(Base):
    """A persisted sea-ice forecast result produced by a forecaster."""

    __tablename__ = "forecasts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    forecast_horizon_days: Mapped[int] = mapped_column(Integer)
    initialization_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True
    )
    region: Mapped[dict] = mapped_column(JSON)
    predicted_concentration: Mapped[dict] = mapped_column(
        JSON,
        comment="Grid of predicted sea-ice concentrations as {lat: [concentrations by lon]} or similar serialized form.",
    )
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    model_version: Mapped[str] = mapped_column(String(64), default="1.0")
    model_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    quality_flags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.utcnow()
    )

    __table_args__ = (
        Index("ix_forecasts_init_horizon", "initialization_time", "forecast_horizon_days"),
    )