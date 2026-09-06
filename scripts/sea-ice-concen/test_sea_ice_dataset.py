from pathlib import Path

from sea_ice_dataset import SeaIceForecastDataset


BASE_DIR = Path(__file__).resolve().parent.parent

TRAIN_FILE = (
    BASE_DIR
    / "processed"
    / "model_ready"
    / "splits"
    / "train.nc"
)


dataset = SeaIceForecastDataset(TRAIN_FILE)

print("Dataset length:", len(dataset))

x, y, y_mask = dataset[0]

print("\nFirst sample:")
print("Input shape: ", tuple(x.shape))
print("Target shape:", tuple(y.shape))
print("Target mask: ", tuple(y_mask.shape))

print("\nInput dtype:", x.dtype)
print("Target dtype:", y.dtype)
print("Mask dtype:", y_mask.dtype)

print("\nSIC channel:")
print("Min:", float(x[:, 0].min()))
print("Max:", float(x[:, 0].max()))

print("\nValidity channel:")
print("Min:", float(x[:, 1].min()))
print("Max:", float(x[:, 1].max()))

print("\nTarget:")
print("Min:", float(y.min()))
print("Max:", float(y.max()))

print("\nTarget valid fraction:", float(y_mask.mean()))

dataset.close()

print("\nSUCCESS: data + missing-value mask works.")