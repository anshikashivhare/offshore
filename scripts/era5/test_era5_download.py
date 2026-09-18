import cdsapi

client = cdsapi.Client()

dataset = "derived-era5-single-levels-daily-statistics"

request = {
    "product_type": "reanalysis",
    "variable": [
        "2m_temperature",
        "10m_u_component_of_wind",
        "10m_v_component_of_wind",
        "surface_pressure",
    ],
    "year": "2025",
    "month": "01",
    "day": [
        "01",
        "02",
        "03",
    ],
    "daily_statistic": "daily_mean",
    "frequency": "1_hour",
    "area": [
        -50,
        -180,
        -90,
        180,
    ],
    "data_format": "netcdf",
}

target = "raw/era5/era5_test_20250101_20250103.nc"

client.retrieve(dataset, request, target)

print("ERA5 test download completed.")
print(f"Saved to: {target}")