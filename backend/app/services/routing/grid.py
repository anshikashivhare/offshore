import math
from typing import Dict, List, Tuple
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
                new_lat = current.lat + dlat
                new_lon = current.lon + dlon
                
                # wrap longitude for the node itself
                if new_lon > 180.0:
                    new_lon -= 360.0
                elif new_lon <= -180.0:
                    new_lon += 360.0

                # Boundary checks for valid coordinates
                if new_lat < -90 or new_lat > 90:
                    continue
                # wrap longitude
                # Calculate shortest longitude difference considering the antimeridian
                dlon_shortest = new_lon - current.lon
                if dlon_shortest > 180:
                    dlon_shortest -= 360
                elif dlon_shortest < -180:
                    dlon_shortest += 360
                    
                # Land avoidance (Robust segment sampling)
                is_safe = True
                
                # Check every edge at approximately 0.05° (~5 km), including
                # coarse global edges.  This prevents a route segment from
                # cutting through a narrow coast between otherwise-water grid
                # nodes.
                dist_deg = math.sqrt(dlat**2 + dlon_shortest**2)
                samples = max(5, int(math.ceil(dist_deg / 0.05)))
                
                # The current node has already been accepted as water during
                # route search.  Start at the first point along the edge so
                # ``snap_to_water`` can move a port that starts on land out to
                # its nearest water cell; all of the proposed edge and its
                # destination remain land-checked.
                for i in range(1, samples + 1):
                    t = i / float(samples)
                    test_lat = current.lat + t * dlat
                    test_lon = current.lon + t * dlon_shortest
                    
                    if test_lon > 180:
                        test_lon -= 360
                    elif test_lon < -180:
                        test_lon += 360
                        
                    if globe.is_land(test_lat, test_lon):
                        is_safe = False
                        break
                        
                if not is_safe:
                    continue

                neighbors.append(Node(new_lat, new_lon))
        return neighbors

    def snap_to_water(self, node: Node, max_radius_degrees: float = 2.0) -> Node | None:
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
        
        # We need a stable BFS. The queue gives us roughly distance order, 
        # but to be truly deterministic and find the absolute closest, we might
        # need to check a full "ring" before returning. 
        # For simplicity and performance, we'll collect all valid water nodes 
        # within max_radius and pick the one with the minimum distance.
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
                        # So any neighbor returned is a valid water node
                        valid_nodes.append(neighbor)

        if not valid_nodes:
            return None
            
        # Find the one with minimum Haversine distance to the original non-aligned coordinate
        return min(valid_nodes, key=lambda n: node.distance_to(n))
