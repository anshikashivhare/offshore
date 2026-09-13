import numpy as np


class TrajectoryPersistenceBaseline:
    """
    Persistence baseline for iceberg trajectories:
    Predicts that the iceberg will not move relative to the ocean current/wind.
    Actually, since the target is 'delta_lat', 'delta_lon', the simplest
    persistence is predicting a delta of 0 (it stops) or predicting the same
    delta as the previous step.

    In the XGBoost model, the naive baseline was delta=0.
    We will use the 'zero movement' baseline as persistence.
    """

    def __init__(self):
        self.name = "Persistence"

    def predict(self, X):
        """
        X is expected to be a DataFrame or array of inputs.
        Returns array of [0, 0] of the same length.
        """
        return np.zeros((len(X), 2))


class SeaIcePersistenceBaseline:
    """
    Persistence baseline for sea-ice concentration:
    Predicts that tomorrow's concentration will be the same as today's.
    """

    def __init__(self):
        self.name = "Persistence"

    def predict(self, X_lag1):
        """
        X_lag1 is the concentration from the previous day.
        Returns the same value.
        """
        return np.array(X_lag1)
