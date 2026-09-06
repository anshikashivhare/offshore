from pathlib import Path
import numpy as np
import xarray as xr


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = (
    BASE_DIR
    / "raw"
    / "nsidc"
    / "2025"
    / "sic_pss25_20250101_am2_v06r00.nc"
)

PROCESSED_FILE = (
    BASE_DIR
    / "processed"
    / "nsidc"
    / "2025"
    / "sic_pss25_20250101_am2_v06r00.nc"
)


# ---------------------------------------------------------
# Open files
# ---------------------------------------------------------

with xr.open_dataset(RAW_FILE) as raw, xr.open_dataset(PROCESSED_FILE) as processed:

    raw_sic = raw["cdr_seaice_conc"]
    processed_sic = processed["sea_ice_concentration"]

    raw_qa = raw["cdr_seaice_conc_qa_flag"]


    # -----------------------------------------------------
    # 1. Dimensions
    # -----------------------------------------------------

    print("=== DIMENSION CHECK ===")

    print("Raw shape:       ", raw_sic.shape)
    print("Processed shape: ", processed_sic.shape)

    assert raw_sic.shape == processed_sic.shape


    # -----------------------------------------------------
    # 2. Coordinates
    # -----------------------------------------------------

    print("\n=== COORDINATE CHECK ===")

    x_match = np.array_equal(
        raw["x"].values,
        processed["x"].values
    )

    y_match = np.array_equal(
        raw["y"].values,
        processed["y"].values
    )

    time_match = np.array_equal(
        raw["time"].values,
        processed["time"].values
    )

    print("X coordinates match:   ", x_match)
    print("Y coordinates match:   ", y_match)
    print("Time coordinates match:", time_match)

    assert x_match
    assert y_match
    assert time_match


    # -----------------------------------------------------
    # 3. QA masking check
    # -----------------------------------------------------

    print("\n=== MASKING CHECK ===")

    invalid_mask = (raw_qa & (8 | 16)) != 0

    raw_nan = np.isnan(raw_sic.values)

    expected_nan = raw_nan | invalid_mask.values
    actual_nan = np.isnan(processed_sic.values)

    correct_masking = np.array_equal(
        expected_nan,
        actual_nan
    )

    print("Raw NaN cells:         ", int(raw_nan.sum()))
    print("QA 8/16 cells:         ", int(invalid_mask.values.sum()))
    print("Expected processed NaN:", int(expected_nan.sum()))
    print("Actual processed NaN:  ", int(actual_nan.sum()))

    print("Correctly masked cells:", correct_masking)

    assert correct_masking


    # -----------------------------------------------------
    # 4. Valid cells
    # -----------------------------------------------------

    print("\n=== VALID DATA CHECK ===")

    raw_valid = np.isfinite(raw_sic.values).sum()
    processed_valid = np.isfinite(processed_sic.values).sum()

    print("Raw valid cells:       ", raw_valid)
    print("Processed valid cells: ", processed_valid)


    # -----------------------------------------------------
    # 5. Range check
    # -----------------------------------------------------

    valid_values = processed_sic.values[np.isfinite(processed_sic.values)]

    print("\n=== RANGE CHECK ===")

    print("Min:", valid_values.min())
    print("Max:", valid_values.max())

    assert valid_values.min() >= 0
    assert valid_values.max() <= 1


    # -----------------------------------------------------
    # 6. QA preservation
    # -----------------------------------------------------

    qa_match = np.array_equal(
        raw_qa.values,
        processed["qa_flag"].values
    )

    print("\n=== QA PRESERVATION ===")

    print("QA flags preserved:", qa_match)

    assert qa_match


print("\nSUCCESS: processed file passed validation.")