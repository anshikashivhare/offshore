from pathlib import Path
import xarray as xr


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

# File is:
# DATA-OFFSHORE/scripts/sea-ice-concen/preprocess_sea_ice_2026.py
# Therefore project root is three levels above this file.

BASE_DIR = Path(__file__).resolve().parent.parent.parent

RAW_DIR = BASE_DIR / "raw" / "nsidc" / "2026"
PROCESSED_DIR = BASE_DIR / "processed" / "nsidc" / "2026"

INVALID_MASK = 8 | 16


# ---------------------------------------------------------
# Create output directory
# ---------------------------------------------------------

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Process one file
# ---------------------------------------------------------

def process_file(input_file: Path) -> bool:

    output_file = PROCESSED_DIR / input_file.name

    print(f"\nProcessing: {input_file.name}")

    try:

        with xr.open_dataset(input_file) as ds:

            # -------------------------------------------------
            # Extract variables
            # -------------------------------------------------

            sic = ds["cdr_seaice_conc"].copy()

            uncertainty = ds["cdr_seaice_conc_stdev"].copy()

            qa = ds["cdr_seaice_conc_qa_flag"].copy()

            spatial_flag = (
                ds["cdr_seaice_conc_interp_spatial_flag"].copy()
            )

            temporal_flag = (
                ds["cdr_seaice_conc_interp_temporal_flag"].copy()
            )

            # -------------------------------------------------
            # Build invalid mask
            # -------------------------------------------------

            invalid_mask = (
                (qa & INVALID_MASK) != 0
            )

            # -------------------------------------------------
            # Apply mask
            # -------------------------------------------------

            sic = sic.where(~invalid_mask)
            uncertainty = uncertainty.where(~invalid_mask)

            # -------------------------------------------------
            # Rename variables
            # -------------------------------------------------

            sic.name = "sea_ice_concentration"
            uncertainty.name = "sea_ice_uncertainty"
            qa.name = "qa_flag"
            spatial_flag.name = "spatial_interpolation_flag"
            temporal_flag.name = "temporal_interpolation_flag"

            # -------------------------------------------------
            # Create processed dataset
            # -------------------------------------------------

            processed = xr.Dataset(
                {
                    "sea_ice_concentration": sic,
                    "sea_ice_uncertainty": uncertainty,
                    "qa_flag": qa,
                    "spatial_interpolation_flag": spatial_flag,
                    "temporal_interpolation_flag": temporal_flag,
                }
            )

            # -------------------------------------------------
            # Preserve metadata
            # -------------------------------------------------

            processed.attrs = dict(ds.attrs)

            processed.attrs["processing_stage"] = "cleaned"

            processed.attrs["invalid_mask_bits"] = "8,16"

            processed.attrs["qa_policy"] = (
                "QA bits 8 (no input data) and "
                "16 (invalid ice mask) are masked. "
                "Bits 1, 2, 4, 32, and 64 are preserved."
            )

            # -------------------------------------------------
            # Compression
            # -------------------------------------------------

            encoding = {
                variable: {
                    "zlib": True,
                    "complevel": 4
                }
                for variable in processed.data_vars
            }

            # -------------------------------------------------
            # Write file
            # -------------------------------------------------

            processed.to_netcdf(
                output_file,
                encoding=encoding
            )

        print(f"[OK] {output_file.name}")
        return True

    except Exception as exc:

        print(f"[ERROR] {input_file.name}")
        print(f"        {exc}")

        if output_file.exists():
            output_file.unlink()

        return False


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    input_files = sorted(RAW_DIR.glob("*.nc"))

    print("=" * 60)
    print("NSIDC 2026 BATCH PREPROCESSING")
    print("=" * 60)

    print(f"Input directory:  {RAW_DIR}")
    print(f"Output directory: {PROCESSED_DIR}")
    print(f"Input files:      {len(input_files)}")
    print()

    success = 0
    failed = 0

    for input_file in input_files:

        if process_file(input_file):
            success += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print("PREPROCESSING SUMMARY")
    print("=" * 60)

    print(f"Total files:      {len(input_files)}")
    print(f"Successful:       {success}")
    print(f"Failed:           {failed}")


if __name__ == "__main__":
    main()