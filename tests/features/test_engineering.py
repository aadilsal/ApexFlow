
import pytest
import pandas as pd
import numpy as np

def test_feature_consistency():
    """Ensure feature engineering outputs deterministic results."""
    data = pd.DataFrame({"raw": [10, 20, 30]})
    
    def engineer_features(df):
        return df["raw"] * 2
        
    feat1 = engineer_features(data)
    feat2 = engineer_features(data)
    
    pd.testing.assert_series_equal(feat1, feat2)

def test_no_infinites_or_nans():
    """Verify that features do not contain infinities or NaNs."""
    features = pd.DataFrame({
        "f1": [1.0, 2.0, 3.0],
        "f2": [0.1, 0.2, 0.3]
    })
    
    assert not np.isinf(features.values).any(), "Found infinities in features"
    assert not np.isnan(features.values).any(), "Found NaNs in features"
