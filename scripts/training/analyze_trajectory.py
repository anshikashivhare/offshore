import pandas as pd
from pathlib import Path

df = pd.read_csv("ml/data/raw/iceberg_trajectory_synthetic_2026.csv")
print("Total rows:", len(df))
print("Unique icebergs:", df['iceberg_id'].nunique())
print("Columns:", list(df.columns))

# Check timestamps per iceberg
counts = df.groupby('iceberg_id').size()
print(f"Min observations per iceberg: {counts.min()}")
print(f"Max observations per iceberg: {counts.max()}")
print(f"Average observations per iceberg: {counts.mean():.2f}")
