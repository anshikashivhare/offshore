# Sea Ice Dataset Data Card

## Dataset Identity

Dataset Name:
NOAA/NSIDC Climate Data Record of Passive Microwave Sea Ice Concentration

Dataset ID:
G02202

Version:
6

Source:
NSIDC / NOAA

DOI:
10.7265/b18j-z797

## Purpose

Project Use:
Sea-ice forecasting and environmental navigation risk assessment.

Primary Variable:
cdr_seaice_conc

## Spatial Information

Region:
Southern Hemisphere / Antarctic

Spatial Resolution:
25 km

CRS:
EPSG:3412

Grid:
Polar stereographic

## Temporal Information

Temporal Resolution:
Daily

Current Test File Date:
2022-01-01

Training Period:
TBD

Validation Period:
TBD

Test Period:
TBD

## Variables

Primary:
cdr_seaice_conc

Uncertainty:
cdr_seaice_conc_stdev

Quality:
cdr_seaice_conc_qa_flag

Spatial Interpolation:
cdr_seaice_conc_interp_spatial_flag

Temporal Interpolation:
cdr_seaice_conc_interp_temporal_flag

Projection:
crs

## Data Quality

Missing Values:
Observed in current file; exact handling TBD.

QA Handling:
TBD

## Processing

Spatial Subset:
TBD

Temporal Subset:
TBD

Missing Value Handling:
TBD

Normalization:
TBD

## Dataset Splits

Training:
TBD

Validation:
TBD

Testing:
TBD

## Limitations

25 km spatial resolution.
Daily temporal resolution.
Quality flags must be considered during preprocessing.

## Notes

Raw source files must never be modified.