import math
import numpy as np
from typing import Dict, List, Tuple, Optional
from functools import lru_cache
from global_land_mask import globe

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

@lru_cache(maxsize=100000)
def _get_valid_neighbors(lat: float, lon: float, resolution: float) -> Tuple[Tuple[float, float], ...]:
    valid_neighbors = []
    
    all_test_lats = []
    all_test_lons = []
    neighbor_sample_counts = []
    neighbor_coords = []
    
    if lat > -50.0:
        step = 2.0
    elif lat > -60.0:
        step = 1.0
    else:
        step = resolution

    for dlat in [-step, 0, step]:
        for dlon in [-step, 0, step]:
            if dlat == 0 and dlon == 0:
                continue
            
            new_lat = lat + dlat
            new_lon = lon + dlon
            
            # wrap longitude for the node itself
            if new_lon > 180.0:
                new_lon -= 360.0
            elif new_lon <= -180.0:
                new_lon += 360.0

            # Boundary checks for valid coordinates
            if new_lat < -90 or new_lat > 90:
                continue
                
            # Calculate shortest longitude difference considering the antimeridian
            dlon_shortest = new_lon - lon
            if dlon_shortest > 180:
                dlon_shortest -= 360
            elif dlon_shortest < -180:
                dlon_shortest += 360
                
            dist_deg = math.sqrt(dlat**2 + dlon_shortest**2)
            samples = max(5, int(math.ceil(dist_deg / 0.05)))
            
            neighbor_sample_counts.append(samples)
            neighbor_coords.append((new_lat, new_lon))
            
            for i in range(1, samples + 1):
                t = i / float(samples)
                test_lat = lat + t * dlat
                test_lon = lon + t * dlon_shortest
                
                if test_lon > 180:
                    test_lon -= 360
                elif test_lon < -180:
                    test_lon += 360
                    
                all_test_lats.append(test_lat)
                all_test_lons.append(test_lon)
                
    if not all_test_lats:
        return ()
        
    lats_np = np.array(all_test_lats)
    lons_np = np.array(all_test_lons)
    
    # Vectorized land check for all neighbors at once
    land_mask = globe.is_land(lats_np, lons_np)
    
    idx = 0
    for i, samples in enumerate(neighbor_sample_counts):
        segment_mask = land_mask[idx:idx+samples]
        if not np.any(segment_mask):
            valid_neighbors.append(neighbor_coords[i])
        idx += samples
        
    return tuple(valid_neighbors)


class GridBuilder:
    def __init__(self, resolution: float = 0.5):
        self.resolution = resolution

    def get_neighbors(self, current: Node) -> List[Node]:
        """Generate 8-way neighbors for a given grid node"""
        coords = _get_valid_neighbors(current.lat, current.lon, self.resolution)
        return [Node(lat, lon) for lat, lon in coords]

    def snap_to_water(self, node: Node, max_radius_degrees: float = 2.0) -> Optional[Node]:
        """Find nearest navigable water node using BFS on the routing grid."""
        
        # Align origin to grid to ensure all waypoints are strictly grid nodes
        grid_lat = round(node.lat / self.resolution) * self.resolution
        grid_lon = round(node.lon / self.resolution) * self.resolution
        grid_node = Node(lat=grid_lat, lon=grid_lon)

        # First check if the given grid node itself is water
        if not globe.is_land(grid_node.lat, grid_node.lon):
            return grid_node

        queue = [(grid_node, 0.0)]
        visited = {grid_node}
        best_node = None
        best_dist = float('inf')

        # Limit BFS to avoid infinite loops, though max_radius handles bounding
        max_iterations = 5000
        iterations = 0
        
        valid_nodes = []

        while queue and iterations < max_iterations:
            iterations += 1
            current, _ = queue.pop(0)

            for neighbor in self.get_neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    
                    dist_deg = math.sqrt((neighbor.lat - grid_node.lat)**2 + (neighbor.lon - grid_node.lon)**2)
                    if dist_deg <= max_radius_degrees:
                        queue.append((neighbor, dist_deg))
                        
                        # get_neighbors already ensures it's navigable water (not land)
                        valid_nodes.append(neighbor)

        if not valid_nodes:
            return None
            
        # Find the one with minimum Haversine distance to the original non-aligned coordinate
        return min(valid_nodes, key=lambda n: node.distance_to(n))
