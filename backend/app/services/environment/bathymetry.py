from app.services.routing.grid import Node

class BathymetryService:
    def get_depth_at(self, lat: float, lon: float) -> float:
        """
        Mock Bathymetry Service.
        Returns the depth of the ocean at the given coordinates in meters.
        Positive values represent depth below sea level.
        In a production environment, this would query GEBCO or ENC datasets.
        """
        # A simple mock: if near the coast of Rothera, depth is shallow (e.g. 10m).
        # Open ocean is deep (e.g. 4000m).
        
        # Rothera bounding box roughly
        if -68.5 <= lat <= -67.0 and -69.0 <= lon <= -67.0:
            return 15.0 # Shallow but navigable water near Rothera
            
        # Sydney harbor entrance roughly
        if -34.0 <= lat <= -33.5 and 151.0 <= lon <= 151.5:
            return 12.0
            
        return 4000.0 # Deep ocean
