"""
Generates a synthetic sea-ice concentration time series for baseline
model development. Structured the same way real NSIDC/Copernicus data
would be (grid cell x date x concentration), so swapping in real data
later only requires replacing this function.
"""

import numpy as np
import pandas as pd


def generate_synthetic_timeseries(rows=20, cols=20, num_days=120, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2025-05-01", periods=num_days, freq="D")

    records = []
    for r in range(rows):
        for c in range(cols):
            base = rng.uniform(0.2, 0.5)
            amplitude = rng.uniform(0.1, 0.3)
            phase_noise = rng.uniform(-5, 5)

            series = np.zeros(num_days)
            prev = base
            for t in range(num_days):
                seasonal = amplitude * np.sin(2 * np.pi * (t + phase_noise) / 180)
                noise = rng.normal(0, 0.02)
                val = 0.7 * prev + 0.3 * (base + seasonal) + noise
                val = np.clip(val, 0.0, 1.0)
                series[t] = val
                prev = val

            for t, date in enumerate(dates):
                records.append({
                    "row": r, "col": c, "date": date,
                    "lat": -65.0 - r * 0.1, "lon": -60.0 + c * 0.1,
                    "concentration": series[t],
                })

    return pd.DataFrame(records)


if __name__ == "__main__":
    df = generate_synthetic_timeseries()
    print(df.shape)
    print(df.head())
