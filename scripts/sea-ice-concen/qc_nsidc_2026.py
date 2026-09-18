from pathlib import Path
import xarray as xr

DATA_DIR = Path("processed/nsidc/2026")

files = sorted(DATA_DIR.glob("*.nc"))

print("=" * 70)
print("NSIDC 2026 QA / COVERAGE CHECK")
print("=" * 70)

anomalies = []

for file in files:

    with xr.open_dataset(file) as ds:

        sic = ds["sea_ice_concentration"]

        total_cells = sic.size
        valid_cells = int(sic.notnull().sum())
        invalid_cells = total_cells - valid_cells
        coverage = valid_cells / total_cells * 100

        date_str = str(ds.time.values[0])[:10]

        print(
            f"{date_str} | "
            f"valid={valid_cells:6d} | "
            f"NaN={invalid_cells:6d} | "
            f"coverage={coverage:6.2f}%"
        )

        # Completely unusable day
        if valid_cells == 0:
            anomalies.append(
                (date_str, valid_cells, coverage)
            )

print("\n" + "=" * 70)
print("ANOMALY SUMMARY")
print("=" * 70)

print(f"Total files checked: {len(files)}")
print(f"Completely invalid dates: {len(anomalies)}")

if anomalies:
    print("\nDates with zero valid SIC:")
    for date_str, valid_cells, coverage in anomalies:
        print(
            f"{date_str} | "
            f"valid={valid_cells} | "
            f"coverage={coverage:.2f}%"
        )
else:
    print("No completely invalid dates found.")

print("\nQC check complete.")