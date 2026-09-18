from pathlib import Path
import numpy as np
import xarray as xr


BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = BASE_DIR / "raw" / "nsidc" / "2025"
PROCESSED_DIR = BASE_DIR / "processed" / "nsidc" / "2025"

DATES = [
    "20250831",
    "20250917",
    "20250922",
    "20251213",
]


for date_str in DATES:

    filename = f"sic_pss25_{date_str}_am2_v06r00.nc"

    raw_file = RAW_DIR / filename
    processed_file = PROCESSED_DIR / filename

    print("\n" + "=" * 70)
    print(f"DATE: {date_str}")
    print("=" * 70)

    with xr.open_dataset(raw_file) as raw, \
         xr.open_dataset(processed_file) as processed:

        raw_sic = raw["cdr_seaice_conc"].values
        raw_qa = raw["cdr_seaice_conc_qa_flag"].values

        proc_sic = processed["sea_ice_concentration"].values

        # Raw statistics
        raw_finite = np.isfinite(raw_sic)

        print("\nRAW DATA")
        print("Shape:", raw_sic.shape)
        print("Finite SIC:", int(raw_finite.sum()))
        print("NaN SIC:", int((~raw_finite).sum()))

        if raw_finite.any():
            print("Raw min:", float(raw_sic[raw_finite].min()))
            print("Raw max:", float(raw_sic[raw_finite].max()))
            print("Raw mean:", float(raw_sic[raw_finite].mean()))

        # QA information
        unique_qa, counts_qa = np.unique(
            raw_qa,
            return_counts=True
        )

        print("\nRAW QA VALUES")

        for value, count in zip(unique_qa, counts_qa):
            print(
                f"QA {int(value):3d}: "
                f"{int(count):6d} cells"
            )

        # Bit masks
        invalid_mask = (raw_qa & (8 | 16)) != 0

        print("\nQA BIT COUNTS")

        print(
            "Bit 8:",
            int(((raw_qa & 8) != 0).sum())
        )

        print(
            "Bit 16:",
            int(((raw_qa & 16) != 0).sum())
        )

        print(
            "Bit 8 or 16:",
            int(invalid_mask.sum())
        )

        # Expected after preprocessing
        expected_valid = raw_finite & ~invalid_mask

        print("\nEXPECTED AFTER CLEANING")
        print("Expected valid:", int(expected_valid.sum()))
        print("Expected NaN:", int((~expected_valid).sum()))

        # Actual processed
        processed_finite = np.isfinite(proc_sic)

        print("\nPROCESSED DATA")
        print("Processed finite:", int(processed_finite.sum()))
        print("Processed NaN:", int((~processed_finite).sum()))

        if processed_finite.any():
            print(
                "Processed min:",
                float(proc_sic[processed_finite].min())
            )
            print(
                "Processed max:",
                float(proc_sic[processed_finite].max())
            )
            print(
                "Processed mean:",
                float(proc_sic[processed_finite].mean())
            )

        # Final consistency check
        print("\nCONSISTENCY")

        print(
            "Valid-cell agreement:",
            np.array_equal(
                expected_valid,
                processed_finite
            )
        )