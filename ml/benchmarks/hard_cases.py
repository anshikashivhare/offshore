from pathlib import Path

import pandas as pd
import yaml


def load_hard_cases_config(config_path=None):
    if config_path is None:
        config_path = Path(__file__).parent / "config.yaml"
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config


def get_trajectory_hard_case_masks(df: pd.DataFrame, config=None):
    """
    Returns a dictionary of boolean masks for each hard case defined in config.
    """
    if config is None:
        config = load_hard_cases_config()

    masks = {"overall": pd.Series([True] * len(df), index=df.index)}

    hard_cases = config.get("trajectory", {}).get("hard_cases", {})
    for case_name, case_config in hard_cases.items():
        try:
            # Using pandas eval for simple conditions like "abs(wind_u) > 0.01"
            mask = df.eval(case_config["condition"])
            masks[case_name] = mask
        except Exception as e:
            print(f"Warning: could not evaluate condition for {case_name}: {e}")

    return masks


def get_seaice_hard_case_masks(df: pd.DataFrame, config=None):
    if config is None:
        config = load_hard_cases_config()

    masks = {"overall": pd.Series([True] * len(df), index=df.index)}

    hard_cases = config.get("sea_ice", {}).get("hard_cases", {})
    for case_name, case_config in hard_cases.items():
        try:
            mask = df.eval(case_config["condition"])
            masks[case_name] = mask
        except Exception as e:
            print(f"Warning: could not evaluate condition for {case_name}: {e}")

    return masks
