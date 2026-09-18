# Offshore Sea-Ice Dataset Collection Progress

## Project Overview
This project involves collecting and processing multimodal environmental data for sea-ice forecasting and environmental navigation risk assessment. The objective is to build a demonstrator dataset focused on the Antarctic region to train and validate machine learning models.

**Prototype Reference Period:**
- **Start:** `2025-01-01`
- **End:** `2026-06-23`
- **Reason:** Selected to reduce data volume while retaining sufficient recent data for pipeline development and time-based validation.

**Spatial Information (Base Grid):**
- **Region:** Southern Hemisphere / Antarctic
- **Grid Type:** Polar Stereographic (EPSG:3412)
- **Resolution:** 25 km
- **Grid Dimensions:** 316 (x) by 332 (y)

---

## Data Collection Goals & Prioritization
Based on the project's requirements, the following modalities are being gathered:

| Data Type | Variables | Priority | Status |
| :--- | :--- | :--- | :--- |
| **Sea-ice concentration** | Concentration %, lat/lon, timestamp | 🔴 Essential | In Progress |
| **Weather** | Wind speed/direction, temp, pressure | 🔴 Essential | In Progress |
| **Ocean currents** | Current u/v, SST, waves | 🔴 Essential | In Progress |
| **Satellite imagery** | SAR/optical, timestamp, geolocation | 🔴 Essential | Pending |
| **Iceberg observations** | ID, lat/lon, timestamp, size/geometry | 🔴 Essential | Pending (USNIC) |
| **Vessel/AIS** | Position, timestamp, speed, heading | 🟡 Important | Pending |
| **Bathymetry** | Depth/elevation | 🟡 Supporting | Pending |
| **Sea-ice drift** | Ice velocity/u-v vectors | 🟡 Very Useful | Pending |

---

## Current Collection Status

### 1. Sea Ice Concentration (NOAA/NSIDC CDR v6)
- **Status:** **Processed**
- **Temporal Resolution:** Daily
- **Progress:** 
  - 2025: 365 raw files downloaded and processed.
  - 2026: 174 raw files downloaded and processed (up to prototype end date).
- **Summary:** The core passive microwave sea ice concentration data has been successfully retrieved and processed for the entire prototype period.

### 2. Meteorological Data (ERA5)
- **Status:** **In Progress**
- **Temporal Resolution:** Hourly
- **Progress:**
  - 2025: Data downloaded and extracted in quarterly chunks (Q1-Q4).
  - 2026: Data downloaded and extracted (Q1, Q2).
  - Additional testing/processing runs are present (`era5_test_20250101_20250103.nc`).
- **Summary:** Raw downloads for the required time window are complete. Processing into the model-ready grid is partially complete/ongoing.

### 3. Oceanographic Data (Copernicus Marine)
- **Status:** **In Progress**
- **Temporal Resolution:** Daily
- **Progress:**
  - 2025: Initial data files downloaded.
  - 2026: Partial data files downloaded.
- **Summary:** Initial automated scripts are in place and successfully pulling data. The collection across the full temporal window is underway.

---

## Integration and Testing
- **1-Day Integration Test (2025-01-01):** Passed ✅
  - Evaluated overlaps across NSIDC, ERA5, and Copernicus Marine for a single day.
  - Confirmed spatial alignment and coordinate coverage across domains:
    - Latitude overlap: `-80.0` to `-50.0`
    - Longitude overlap: `-180.0` to `179.75`
    - Native `EPSG:3412` grid retained for NSIDC.

## Next Steps
1. **Complete Copernicus Marine Downloads:** Finish fetching the daily oceanographic fields for 2025 and 2026.
2. **Standardization / Regridding:** Ensure all meteorological (ERA5) and oceanographic (Copernicus) data is fully re-projected and interpolated onto the native NSIDC polar stereographic grid.
3. **Iceberg Data:** Begin the collection pipeline for USNIC iceberg locations and observations for the prototype period.
4. **Compile Model-Ready Dataset:** Finalize the merging of processed sources into the `processed/model_ready` splits.
