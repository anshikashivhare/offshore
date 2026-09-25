from abc import ABC, abstractmethod
from typing import List, Dict, Any

class VesselProvider(ABC):
    @abstractmethod
    def get_vessel(self, vessel_id: str) -> Dict[str, Any]:
        """
        Returns vessel properties including draft, max_speed, and constraints.
        Must raise ValueError if vessel_id is not found.
        """
        pass

class PortProvider(ABC):
    @abstractmethod
    def get_port(self, port_id: str) -> Dict[str, Any]:
        """
        Returns port properties including lat, lon, and name.
        """
        pass
        
class IcebergProvider(ABC):
    @abstractmethod
    def get_candidate_icebergs(self, bounds: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Accepts a spatial bounding box (min_lat, min_lon, max_lat, max_lon).
        Returns a list of recent iceberg observations (lat, lon, iceberg_id, timestamp).
        """
        pass
