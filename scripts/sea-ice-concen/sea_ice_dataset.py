from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset
import xarray as xr


class SeaIceForecastDataset(Dataset):
    """
    Lazy-loading PyTorch dataset for sea-ice forecasting.

    Input:
        7 consecutive days

    Each day has 2 channels:
        Channel 0 = sea-ice concentration
        Channel 1 = valid-data mask

    Input shape:
        (7, 2, 332, 316)

    Target:
        Next-day sea-ice concentration

    Target shape:
        (332, 316)
    """

    def __init__(self, netcdf_file):
        self.netcdf_file = Path(netcdf_file)

        if not self.netcdf_file.exists():
            raise FileNotFoundError(
                f"Dataset not found: {self.netcdf_file}"
            )

        self.ds = xr.open_dataset(
            self.netcdf_file,
            cache=False
        )

        self.inputs = self.ds[
            "input_sea_ice_concentration"
        ]

        self.targets = self.ds[
            "target_sea_ice_concentration"
        ]

    def __len__(self):
        return self.ds.sizes["sample"]

    def __getitem__(self, index):

        # -------------------------------------------------
        # Read one sample only
        # -------------------------------------------------

        x = self.inputs.isel(sample=index).values
        y = self.targets.isel(sample=index).values

        # -------------------------------------------------
        # Create validity masks BEFORE filling NaNs
        # -------------------------------------------------

        x_valid = np.isfinite(x).astype(np.float32)
        y_valid = np.isfinite(y).astype(np.float32)

        # -------------------------------------------------
        # Fill missing SIC with zero
        # -------------------------------------------------

        x = np.nan_to_num(
            x,
            nan=0.0,
            posinf=0.0,
            neginf=0.0
        )

        y = np.nan_to_num(
            y,
            nan=0.0,
            posinf=0.0,
            neginf=0.0
        )

        # -------------------------------------------------
        # Add mask as second channel
        #
        # x shape:
        # (7, H, W)
        #
        # after stacking:
        # (7, 2, H, W)
        # -------------------------------------------------

        x = np.stack(
            [x, x_valid],
            axis=1
        )

        # -------------------------------------------------
        # Convert to PyTorch tensors
        # -------------------------------------------------

        x = torch.tensor(
            x,
            dtype=torch.float32
        )

        y = torch.tensor(
            y,
            dtype=torch.float32
        )

        y_valid = torch.tensor(
            y_valid,
            dtype=torch.float32
        )

        return x, y, y_valid

    def close(self):
        self.ds.close()