import sys
from pathlib import Path
_root = str(Path(__file__).resolve().parents[0] / "backend")
if _root not in sys.path:
    sys.path.insert(0, _root)

from global_land_mask import globe

def find_water(lat, lon, name="Point"):
    if not globe.is_land(lat, lon):
        print(f"{name} ({lon},{lat}) is WATER")
        return lon, lat
    else:
        print(f"{name} ({lon},{lat}) is LAND. Searching nearby...")
        for r in [0.5, 1.0, 1.5, 2.0, 3.0, 4.0]:
            for dlat in [-r, 0, r]:
                for dlon in [-r, 0, r]:
                    nlat = lat + dlat
                    nlon = lon + dlon
                    if not globe.is_land(nlat, nlon):
                        print(f"  Found water at ({nlon},{nlat}) at radius {r}")
                        return nlon, nlat
        print("  Could not find water!")
        return None

if __name__ == "__main__":
    find_water(57.1497, -2.0943, "Aberdeen")
    find_water(-67.5695, -68.1250, "Rothera")
    find_water(-33.8688, 151.2093, "Sydney")
