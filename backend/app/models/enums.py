import enum

class AlertSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(str, enum.Enum):
    DATASET_INGESTION = "dataset_ingestion"
    RASTER_PREPROCESSING = "raster_preprocessing"
    ICEBERG_DETECTION = "iceberg_detection"
    SEA_ICE_FORECASTING = "sea_ice_forecasting"
    TRAJECTORY_PREDICTION = "trajectory_prediction"
    RISK_GENERATION = "risk_generation"
    ROUTE_GENERATION = "route_generation"

class ObjectiveType(str, enum.Enum):
    FASTEST = "fastest"
    SAFEST = "safest"
    FUEL_EFFICIENT = "fuel_efficient"
    SHORTEST = "shortest"

class RiskCategory(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    AVOID = "avoid"
