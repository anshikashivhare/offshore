import cdsapi
from pathlib import Path
import sys

if len(sys.argv) != 2:
    print("Usage: python download_era5_month.py MM")
    print("Example: python download_era5_month.py 01")
    sys.exit(1)

month = sys.argv[1]

if month not in {f"{i:02d}" for i in range(1, 13)}:
    print("Month must be between 01 and 12.")
    sys.exit(1)

output_dir = Path("raw/era5/2025")
output_dir.mkdir(parents=True, exist_ok=True)

target = output_dir / f"era5_2025_{month}.zip"

client = cdsapi.Client()

request = {
    "product_type": "reanalysis",
    "variable": [
        "2m_temperature",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "surface_pressure",
    ],
    "year": "2025",
    "month": month,
    "day": [f"{i:02d}" for i in range(1, 32)],
    "daily_statistic": "daily_mean",
    "frequency": "1_hour",
    "area": [-50, -180, -90, 180],
    "data_format": "netcdf",
}

print(f"Requesting ERA5: 2025-{month}")
print(f"Target: {target}")

client.retrieve(
    "derived-era5-single-levels-daily-statistics",
    request,
    str(target),
)

print("Download completed.")
print(f"Saved: {target}")