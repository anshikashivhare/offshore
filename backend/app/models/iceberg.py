import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.base import Base
from geoalchemy2 import Geometry
from sqlalchemy import JSON, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Iceberg(Base):
    __tablename__ = "icebergs"

    iceberg_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Could store initial detection or other static properties here

    detections: Mapped[List["IcebergDetection"]] = relationship(
        back_populates="iceberg", cascade="all, delete-orphan"
    )
    predictions: Mapped[List["IcebergTrajectoryPrediction"]] = relationship(
        back_populates="iceberg", cascade="all, delete-orphan"
    )


class IcebergDetection(Base):
    __tablename__ = "iceberg_detections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    iceberg_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("icebergs.iceberg_id"), index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    geometry: Mapped[str] = mapped_column(Geometry("POINT", srid=4326), index=True)
    estimated_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    extent: Mapped[Optional[Any]] = mapped_column(
        Geometry("POLYGON", srid=4326), nullable=True
    )
    confidence: Mapped[float] = mapped_column(Float)
    source_imagery: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    detection_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )

    iceberg: Mapped["Iceberg"] = relationship(back_populates="detections")


class IcebergTrajectoryPrediction(Base):
    __tablename__ = "iceberg_predictions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    iceberg_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("icebergs.iceberg_id"), index=True
    )
    prediction_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True
    )
    forecast_horizon: Mapped[int] = mapped_column(comment="Forecast horizon in hours")
    forecast_horizon_unit: Mapped[str] = mapped_column(String(16), default="hours")
    predicted_geometry: Mapped[str] = mapped_column(
        Geometry("POINT", srid=4326),
        index=True,
        comment="Final predicted centroid position at forecast_horizon.",
    )
    predicted_path: Mapped[Optional[List[List[float]]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Full predicted trajectory as [[lon, lat], ...] (LINESTRING in JSON).",
    )
    uncertainty_representation: Mapped[Optional[str]] = mapped_column(
        Geometry("POLYGON", srid=4326), nullable=True
    )
    model_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    iceberg: Mapped["Iceberg"] = relationship(back_populates="predictions")
