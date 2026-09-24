import uuid
from datetime import datetime
from typing import Optional

from app.models.base import Base
from app.models.enums import ObjectiveType
from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Route(Base):
    __tablename__ = "routes"

    route_id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    origin: Mapped[str] = mapped_column(String(255))
    destination: Mapped[str] = mapped_column(String(255))
    vessel_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("vessels.vessel_id"), index=True
    )
    departure_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    geometry: Mapped[str] = mapped_column(Geometry("LINESTRING", srid=4326), index=True)
    distance: Mapped[float] = mapped_column(Float, comment="distance in nautical miles")
    eta: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    travel_time: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    estimated_fuel: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[float] = mapped_column(Float)
    risk_exposure: Mapped[float] = mapped_column(Float, nullable=True, default=0.0)
    objective_type: Mapped[ObjectiveType] = mapped_column(Enum(ObjectiveType))
    algorithm_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
