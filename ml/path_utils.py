import os


def get_model_dir() -> str:
    """
    Returns the directory to save models to.
    Uses OFFSHORE_MODEL_DIR env var if set, otherwise defaults to ml/models/weights.
    """
    return os.environ.get("OFFSHORE_MODEL_DIR", "ml/models/weights")


def get_mlops_dir() -> str:
    """
    Returns the directory to save mlops logs to.
    Uses OFFSHORE_MLOPS_DIR env var if set, otherwise defaults to mlops.
    """
    return os.environ.get("OFFSHORE_MLOPS_DIR", "mlops")


def get_model_path(filename: str) -> str:
    """Returns the full path for a model file."""
    # Ensure directory exists
    dir_path = get_model_dir()
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, filename)


def get_mlops_path(filename: str) -> str:
    """Returns the full path for an mlops file."""
    # Ensure directory exists
    dir_path = get_mlops_dir()
    os.makedirs(dir_path, exist_ok=True)
    return os.path.join(dir_path, filename)
