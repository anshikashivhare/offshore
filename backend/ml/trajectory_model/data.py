"""
Generates synthetic iceberg trajectory data: a set of icebergs drifting
under the influence of ocean current + wind, with some noise. Structured
so it can be swapped for real NSIDC iceberg tracking data later.
"""

import numpy as np
import pandas as pd


def generate_synthetic_tracks(num_icebergs=30, num_steps=60, seed=42):
    rng = np.random.default_rng(seed)
    records = []

    for iceberg_id in range(num_icebergs):
        lat = rng.uniform(-70, -62)
        lon = rng.uniform(-65, -50)

        current_u = rng.uniform(-0.02, 0.02)
        current_v = rng.uniform(-0.01, 0.01)
        wind_u = rng.uniform(-0.01, 0.01)
        wind_v = rng.uniform(-0.005, 0.005)

        for t in range(num_steps):
            noise_lat = rng.normal(0, 0.003)
            noise_lon = rng.normal(0, 0.003)

            delta_lat = 0.6 * current_v + 0.3 * wind_v + noise_lat
            delta_lon = 0.6 * current_u + 0.3 * wind_u + noise_lon

            records.append({
                "iceberg_id": iceberg_id,
                "timestep": t,
                "lat": lat,
                "lon": lon,
                "current_u": current_u,
                "current_v": current_v,
                "wind_u": wind_u,
                "wind_v": wind_v,
                "next_delta_lat": delta_lat,
                "next_delta_lon": delta_lon,
            })

            lat += delta_lat
            lon += delta_lon

    return pd.DataFrame(records)


if __name__ == "__main__":
    df = generate_synthetic_tracks()
    print(df.shape)
    print(df.head())
