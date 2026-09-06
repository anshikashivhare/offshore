from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime

class DataSource(ABC):
    """Metadata describing the data source."""
    name: str
    description: str
    homepage: str

class DataFetcher(ABC):
    """Interface for pulling/downloading raw data."""
    
    @abstractmethod
    async def fetch(self, **kwargs) -> Any:
        """Fetch raw data (e.g. bytes, JSON, xarray Dataset)"""
        pass

class DataValidator(ABC):
    """Interface for validating metadata, completeness, and structure."""
    
    @abstractmethod
    def validate(self, raw_data: Any) -> bool:
        """Return True if data is structurally valid, raise exception otherwise."""
        pass

class DataNormalizer(ABC):
    """Interface for harmonizing units, datatypes, and missing values."""
    
    @abstractmethod
    def normalize(self, raw_data: Any) -> Any:
        """Convert raw data into a standardized intermediate format."""
        pass

class SpatialAligner(ABC):
    """Interface for clipping bounding boxes and standardizing CRS."""
    
    @abstractmethod
    def align_spatial(self, normalized_data: Any, bbox: Optional[tuple] = None) -> Any:
        """Ensure CRS is EPSG:4326 and optionally clip to bounding box."""
        pass

class TemporalAligner(ABC):
    """Interface for filtering and normalizing timestamps."""
    
    @abstractmethod
    def align_temporal(self, spatial_aligned_data: Any, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Any:
        """Ensure timestamps are UTC ISO8601 and filter by time range."""
        pass
