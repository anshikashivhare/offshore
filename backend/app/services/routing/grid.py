import math
from typing import Dict, List, Tuple, Optional
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
        # Multi-resolution: coarse near equator, fine near Antarctica
        if current.lat > -50.0:
            step = 2.0
        elif current.lat > -60.0:
            step = 1.0
        else:
            step = self.resolution

        for dlat in [-step, 0, step]:
            for dlon in [-step, 0, step]:
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
                # Geodesic interpolation
                # A simple approximation for small distances (< 10 degrees)
                # We can just interpolate linearly in lat/lon, BUT we must be careful at high latitudes.
                # Actually, geographiclib is best, but we can just use linear for now and flag it?
                # The prompt asks for geodesic interpolation.
                for i in range(1, samples + 1):
                    t = i / float(samples)
                    
                    # Haversine-based intermediate point (approximate geodesic)
                    lat1 = math.radians(current.lat)
                    lon1 = math.radians(current.lon)
                    lat2 = math.radians(current.lat + dlat)
                    lon2 = math.radians(current.lon + dlon_shortest)
                    
                    dist_rad = math.sqrt( (lat2-lat1)**2 + (math.cos((lat1+lat2)/2)*(lon2-lon1))**2 )
                    
                    if dist_rad < 1e-6:
                        test_lat = current.lat
                        test_lon = current.lon
                    else:
                        A = math.sin((1 - t) * dist_rad) / math.sin(dist_rad)
                        B = math.sin(t * dist_rad) / math.sin(dist_rad)
                        x = A * math.cos(lat1) * math.cos(lon1) + B * math.cos(lat2) * math.cos(lon2)
                        y = A * math.cos(lat1) * math.sin(lon1) + B * math.cos(lat2) * math.sin(lon2)
                        z = A * math.sin(lat1) + B * math.sin(lat2)
                        
                        test_lat = math.degrees(math.atan2(z, math.sqrt(x*x + y*y)))
                        test_lon = math.degrees(math.atan2(y, x))
                        
                    if test_lon > 180:
                        test_lon -= 360
                    elif test_lon <= -180:
                        test_lon += 360
                        
                    if globe.is_land(test_lat, test_lon):
                        is_safe = False
                        break
                        
                if not is_safe:
                    continue

                neighbors.append(Node(new_lat, new_lon))
        return neighbors

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
