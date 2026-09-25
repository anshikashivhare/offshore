from typing import List, Dict, Any
import datetime
from .interfaces import VesselProvider, PortProvider, IcebergProvider

class DemoVesselProvider(VesselProvider):
    def get_vessel(self, vessel_id: str) -> Dict[str, Any]:
        return {
            "vessel_id": vessel_id,
            "max_speed_knots": 15.0,
            "draft_m": 8.0,
            "source": "synthetic_demo"
        }

class DemoPortProvider(PortProvider):
    def get_port(self, port_id: str) -> Dict[str, Any]:
        # Provide deterministic mock endpoints
        return {
            "port_id": port_id,
            "name": "Demo Port",
            "lat": -60.0,
            "lon": -60.0,
            "source": "synthetic_demo"
        }

class DemoIcebergProvider(IcebergProvider):
    def get_candidate_icebergs(self, bounds: Dict[str, float]) -> List[Dict[str, Any]]:
        # Provide deterministic mock candidates inside bounds
        return [
            {
                "iceberg_id": "demo-iceberg-1",
                "lat": bounds.get("min_lat", -65.0) + 1.0,
                "lon": bounds.get("min_lon", -65.0) + 1.0,
                "timestamp": datetime.datetime.utcnow(),
                "source": "synthetic_demo"
            }
        ]
