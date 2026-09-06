from pathlib import Path
import numpy as np
import xarray as xr

BASE_DIR = Path(__file__).resolve().parent.parent
FILE = BASE_DIR / "processed" / "sea_ice_20220101_processed.nc"

ds = xr.open_dataset(FILE)

qa = ds["qa_flag"].values

flags = {
    1: "BT weather filter",
    2: "NT weather filter",
    4: "Land spillover filter",
    8: "No input data",
    16: "Invalid ice mask",
    32: "Spatial interpolation",
    64: "Temporal interpolation",
}

print("========== QA BIT ANALYSIS ==========\n")

total = qa.size

for mask, meaning in flags.items():
    count = np.count_nonzero((qa & mask) != 0)
    percentage = count / total * 100

    print(
        f"{mask:2d} | {meaning:25s} | "
        f"{count:6d} cells | {percentage:6.2f}%"
    )

ds.close()