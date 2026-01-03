import pandas as pd
import numpy as np
from typing import Iterator, Tuple

class TimeAwareSplitter:
    """
    Custom Cross-Validator that respects time order:
    Train on past -> Test on future.
    """
    def __init__(self, n_splits: int = 5):
        self.n_splits = n_splits

    def split(self, X: pd.DataFrame, y=None, groups=None) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        """
        Expects X to be sorted by time or have metadata cols.
        For F1, we usually split by Weekend or Session.
        Assumption: X is sorted by Date/SessionTime.
        """
        # We assume X has an index or column 'Date' or is pre-sorted.
        # If not, we should sort internally, but that requires copy.
        # Simple TimeSeriesSplit approach from sklearn can be used if sorted.
        
        from sklearn.model_selection import TimeSeriesSplit
        tscv = TimeSeriesSplit(n_splits=self.n_splits)
        
        for train_index, test_index in tscv.split(X):
            yield train_index, test_index

splitter = TimeAwareSplitter()
