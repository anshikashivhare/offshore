import math
from typing import Dict, List, Tuple


class Node:
    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon

    def __eq__(self, other):
        # Allow small floating point tolerance for equality
        return abs(self.lat - other.lat) < 1e-5 and abs(self.lon - other.lon) < 1e-5

    def __hash__(self):
        return hash((round(self.lat, 4), round(self.lon, 4)))

    def distance_to(self, other: "Node") -> float:
        """Haversine distance in nautical miles"""
        R = 3440.065  # Radius of earth in NM
        dlat = math.radians(other.lat - self.lat)
        dlon = math.radians(other.lon - self.lon)
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(
            math.radians(self.lat)
        ) * math.cos(math.radians(other.lat)) * math.sin(dlon / 2) * math.sin(dlon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c


class GridBuilder:
    def __init__(self, resolution: float = 0.5):
        self.resolution = resolution

    def get_neighbors(self, current: Node) -> List[Node]:
        """Generate 8-way neighbors for a given grid node"""
        neighbors = []
        for dlat in [-self.resolution, 0, self.resolution]:
            for dlon in [-self.resolution, 0, self.resolution]:
                if dlat == 0 and dlon == 0:
                    continue
                # Simple Cartesian-like step for this example.
                # In real life, longitude spacing depends on latitude.
                neighbors.append(Node(current.lat + dlat, current.lon + dlon))
        return neighbors
