import json
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def load_reference_statistics(filepath: str) -> dict:
    """
    Load reference statistics from a JSON file.
    These statistics should describe the expected distribution or summary stats
    of the training data to compare against new incoming data.
    """
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load reference statistics from {filepath}: {e}")
        raise


def detect_drift(
    new_data_df: pd.DataFrame, ref_stats: dict, drift_columns: list
) -> list:
    """
    Compare new data against reference statistics to detect potential data drift.

    Args:
        new_data_df: DataFrame containing new data to check
        ref_stats: Dictionary containing reference statistics (e.g. mean, std from training)
        drift_columns: List of columns to check for drift

    Returns:
        A list of warnings. If empty, no drift detected.
    """
    warnings = []

    # Placeholder implementation:
    # In a real scenario, you might compute KS-statistics or compare means/variances.
    for col in drift_columns:
        if col not in new_data_df.columns:
            warnings.append(f"Column '{col}' missing from new data")
            continue

        # Example check (replace with actual drift detection logic):
        if col in ref_stats:
            expected_mean = ref_stats[col].get("mean")
            if expected_mean is not None:
                actual_mean = new_data_df[col].mean()

                # Simple heuristic: alert if mean shifts by more than 20%
                if expected_mean != 0:
                    shift = abs(actual_mean - expected_mean) / abs(expected_mean)
                    if shift > 0.20:
                        warnings.append(
                            f"Drift detected in '{col}': mean shifted by {shift:.1%}"
                        )

    return warnings
