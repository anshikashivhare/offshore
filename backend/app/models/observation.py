import uuid
from datetime import datetime
from typing import Optional

from app.models.base import Base
from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, Index, String
from sqlalchemy.orm import Mapped, mapped_column


class SeaIceObservation(Base):
    __tablename__ = "sea_ice_observations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    geometry: Mapped[str] = mapped_column(Geometry("POLYGON", srid=4326), index=True)
    concentration: Mapped[float] = mapped_column(Float)
    thickness: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ice_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source: Mapped[str] = mapped_column(String(255))
    data_quality: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True, comment="Confidence score 0-1"
    )


class WeatherObservation(Base):
    __tablename__ = "weather_observations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    geometry: Mapped[str] = mapped_column(Geometry("POINT", srid=4326), index=True)
    wind_speed: Mapped[float] = mapped_column(Float)
    wind_direction: Mapped[float] = mapped_column(Float)
    temperature: Mapped[float] = mapped_column(Float)
    wave_height: Mapped[float] = mapped_column(Float)
    pressure: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(255))


class OceanObservation(Base):
    __tablename__ = "ocean_observations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    geometry: Mapped[str] = mapped_column(Geometry("POINT", srid=4326), index=True)
    current_speed: Mapped[float] = mapped_column(Float)
    current_direction: Mapped[float] = mapped_column(Float)
    sea_surface_temperature: Mapped[float] = mapped_column(Float)
    wave_information: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(String(255))
