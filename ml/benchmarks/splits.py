import pandas as pd


def time_based_split_strict(
    df: pd.DataFrame, val_frac=0.15, test_frac=0.15, sort_col="date"
):
    """
    Splits a dataframe strictly chronologically to prevent sequence overlap leakage.
    Must be called BEFORE any sequence window generation.
    """
    df = df.sort_values(sort_col).copy()
    val_cutoff = df[sort_col].quantile(
        1 - (val_frac + test_frac), interpolation="nearest"
    )
    test_cutoff = df[sort_col].quantile(1 - test_frac, interpolation="nearest")

    train = df[df[sort_col] < val_cutoff].copy()
    val = df[(df[sort_col] >= val_cutoff) & (df[sort_col] < test_cutoff)].copy()
    test = df[df[sort_col] >= test_cutoff].copy()

    return train, val, test


def time_based_split_per_entity_strict(
    df: pd.DataFrame, entity_col="iceberg_id", val_frac=0.15, test_frac=0.15
):
    """
    Splits trajectory data per entity (e.g. iceberg_id) chronologically to ensure
    that the early part of an iceberg's life is training, middle is validation,
    and end is test. Must be called BEFORE sequence window generation.
    """
    train_frames, val_frames, test_frames = [], [], []
    for _, group in df.groupby(entity_col):
        # Already assume it's sorted by time (timestep or date)
        val_cutoff = int(len(group) * (1 - (val_frac + test_frac)))
        test_cutoff = int(len(group) * (1 - test_frac))

        train_frames.append(group.iloc[:val_cutoff].copy())
        val_frames.append(group.iloc[val_cutoff:test_cutoff].copy())
        test_frames.append(group.iloc[test_cutoff:].copy())

    return pd.concat(train_frames), pd.concat(val_frames), pd.concat(test_frames)
