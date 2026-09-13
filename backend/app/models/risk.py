import uuid
from datetime import datetime

from app.models.base import Base
from geoalchemy2 import Geometry
from sqlalchemy import JSON, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column


class RiskCell(Base):
    __tablename__ = "risk_cells"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    geometry: Mapped[str] = mapped_column(Geometry("POLYGON", srid=4326), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ice_risk: Mapped[float] = mapped_column(Float)
    iceberg_risk: Mapped[float] = mapped_column(Float)
    weather_risk: Mapped[float] = mapped_column(Float)
    current_risk: Mapped[float] = mapped_column(Float)
    composite_risk: Mapped[float] = mapped_column(Float)
    risk_category: Mapped[str] = mapped_column(String(50))
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    missing_data_flags: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_info: Mapped[dict] = mapped_column(JSON, default=dict)
