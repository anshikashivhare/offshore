import uuid
from datetime import datetime
from typing import Optional

from app.models.base import Base
from geoalchemy2 import Geometry
from sqlalchemy import JSON, DateTime, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class RiskCell(Base):
    __tablename__ = "risk_cells"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    geometry: Mapped[str] = mapped_column(Geometry("POLYGON", srid=4326), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ice_risk: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    iceberg_risk: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    weather_risk: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    current_risk: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    composite_risk: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    risk_category: Mapped[str] = mapped_column(String(50))
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    missing_data_flags: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_info: Mapped[dict] = mapped_column(JSON, default=dict)
    data_source: Mapped[str] = mapped_column(String(50), default="observation")

    __table_args__ = (
        UniqueConstraint("geometry", "timestamp", name="uix_risk_cell_geom_time"),
    )
