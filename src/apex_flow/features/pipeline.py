import pandas as pd
from typing import List, Dict, Any
from apex_flow.features.base import BaseFeatureTransformer
from apex_flow.features.transformers import FuelAdjustedLapTime, TrackEvolution, WeatherImpact

class FeaturePipeline:
    def __init__(self):
        self.transformers: List[BaseFeatureTransformer] = [
            FuelAdjustedLapTime(),
            TrackEvolution(),
            WeatherImpact()
        ]
        
    def process_dataframe(self, df: pd.DataFrame, context: Dict[str, Any] = None) -> pd.DataFrame:
        df_processed = df.copy()
        for transformer in self.transformers:
            df_processed = transformer.fit_transform(df_processed, context)
        return df_processed

feature_pipeline = FeaturePipeline()
