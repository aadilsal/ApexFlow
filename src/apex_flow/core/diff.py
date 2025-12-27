import pandas as pd
from pathlib import Path
from typing import Dict, Any

class DiffTool:
    
    @staticmethod
    def compare_parquet(file_a: Path, file_b: Path) -> Dict[str, Any]:
        if not file_a.exists() or not file_b.exists():
            return {"error": "One or both files do not exist"}
            
        df_a = pd.read_parquet(file_a)
        df_b = pd.read_parquet(file_b)
        
        diff_info = {
            "rows_a": len(df_a),
            "rows_b": len(df_b),
            "columns_diff": list(set(df_a.columns) - set(df_b.columns)),
            "numeric_drift": {}
        }
        
        # Check numeric drift for common columns
        common_cols = list(set(df_a.columns) & set(df_b.columns))
        numeric_cols = df_a[common_cols].select_dtypes(include=['float', 'int']).columns
        
        for col in numeric_cols:
            mean_a = df_a[col].mean()
            mean_b = df_b[col].mean()
            diff_pct = 0
            if mean_a != 0:
                 diff_pct = (mean_b - mean_a) / mean_a
            
            diff_info["numeric_drift"][col] = {
                "mean_a": float(mean_a),
                "mean_b": float(mean_b),
                "diff_pct": float(diff_pct)
            }
            
        return diff_info
