from pathlib import Path

import torch
from torch.utils.data import DataLoader

from sea_ice_dataset import SeaIceForecastDataset


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

TRAIN_FILE = (
    BASE_DIR
    / "processed"
    / "model_ready"
    / "splits"
    / "train.nc"
)

VALIDATION_FILE = (
    BASE_DIR
    / "processed"
    / "model_ready"
    / "splits"
    / "validation.nc"
)

TEST_FILE = (
    BASE_DIR
    / "processed"
    / "model_ready"
    / "splits"
    / "test.nc"
)


# ---------------------------------------------------------
# Evaluate persistence
# ---------------------------------------------------------

def evaluate(dataset_file):

    dataset = SeaIceForecastDataset(dataset_file)

    loader = DataLoader(
        dataset,
        batch_size=1,
        shuffle=False,
    )

    total_error = 0.0
    total_valid = 0

    with torch.no_grad():

        for x, y, y_mask in loader:

            # x shape:
            # (batch, 7, 2, H, W)

            # Channel 0 = SIC
            # Channel 1 = validity mask

            # Last input day
            prediction = x[:, -1, 0]

            # Absolute error
            error = torch.abs(
                prediction - y
            )

            # Only valid target cells
            valid_error = error * y_mask

            total_error += valid_error.sum().item()
            total_valid += y_mask.sum().item()

    dataset.close()

    return total_error / total_valid


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

print("=" * 60)
print("SEA-ICE PERSISTENCE BASELINE")
print("=" * 60)

train_mae = evaluate(TRAIN_FILE)
val_mae = evaluate(VALIDATION_FILE)
test_mae = evaluate(TEST_FILE)

print("\nRESULTS")
print("-" * 60)

print(f"Train MAE:       {train_mae:.6f}")
print(f"Validation MAE:  {val_mae:.6f}")
print(f"Test MAE:        {test_mae:.6f}")

print("\nBaseline definition:")
print("Tomorrow's SIC = today's SIC")