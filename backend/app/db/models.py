from sqlalchemy import Column, Integer, Float, Date, String
from geoalchemy2 import Geometry
from app.db.database import Base


class SeaIceObservation(Base):
    __tablename__ = "seaice_observations"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    concentration = Column(Float, nullable=False)  # 0.0 - 1.0
    location = Column(Geometry(geometry_type="POINT", srid=4326))


class IcebergTrack(Base):
    __tablename__ = "iceberg_tracks"

    id = Column(Integer, primary_key=True, index=True)
    iceberg_id = Column(String, index=True, nullable=False)
    timestamp = Column(Date, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    location = Column(Geometry(geometry_type="POINT", srid=4326))


class VesselRoute(Base):
    __tablename__ = "vessel_routes"

    id = Column(Integer, primary_key=True, index=True)
    start_lat = Column(Float, nullable=False)
    start_lon = Column(Float, nullable=False)
    end_lat = Column(Float, nullable=False)
    end_lon = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=True)
    path_json = Column(String, nullable=True)  # store the path as JSON string for now


class EnvironmentalData(Base):
    __tablename__ = "environmental_data"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    current_u = Column(Float, nullable=False)
    current_v = Column(Float, nullable=False)
    wind_u = Column(Float, nullable=False)
    wind_v = Column(Float, nullable=False)
    location = Column(Geometry(geometry_type="POINT", srid=4326))
