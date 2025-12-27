from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional, List, Dict, Any

class BaseFeatureTransformer(ABC):
    """
    Base class for all feature transformers.
    Enforces interface for transforming raw telemetry into features.
    """
    
    @abstractmethod
    def fit(self, df: pd.DataFrame, context: Dict[str, Any] = None):
        pass

    @abstractmethod
    def transform(self, df: pd.DataFrame, context: Dict[str, Any] = None) -> pd.DataFrame:
        pass
        
    def fit_transform(self, df: pd.DataFrame, context: Dict[str, Any] = None) -> pd.DataFrame:
        self.fit(df, context)
        return self.transform(df, context)
