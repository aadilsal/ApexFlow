import xgboost as xgb
import optuna
import pandas as pd
import joblib
from pathlib import Path
from typing import Dict, Any, Optional
from apex_flow.logger import logger
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from apex_flow.modeling.splitter import splitter

from apex_flow.tracking.experiment_manager import experiment_manager
from apex_flow.features.pipeline import feature_pipeline

class ModelTrainer:
    def __init__(self, model_dir: str = "models"):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        # Path to the most recent saved model for warm‑start
        self.prev_model_path = self.model_dir / "best_model.joblib"
        
    def train(self, df_raw: pd.DataFrame, trial_count: int = 10, study_name: str = "lap_time_optimization", warm_start: bool = False) -> Any:
        logger.info("training_start", shape=df_raw.shape)
        
        # Unified Feature Engineering
        df_processed = feature_pipeline.process_dataframe(df_raw)
        X = df_processed.drop(columns=["lap_time", "timestamp"], errors='ignore')
        y = df_raw["lap_time"]
        
        # Start MLflow run
        with experiment_manager.start_run():
            # Log Data info
            experiment_manager.log_params({"n_samples": len(X), "n_features": X.shape[1]})
            # Ideally log DVC hash or Git commit here if available
        
            def objective(trial):
                param = {
                    'verbosity': 0,
                    'objective': 'reg:squarederror',
                    'booster': 'gbtree',
                    'lambda': trial.suggest_float('lambda', 1e-8, 1.0, log=True),
                    'alpha': trial.suggest_float('alpha', 1e-8, 1.0, log=True),
                    'subsample': trial.suggest_float('subsample', 0.2, 1.0),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.2, 1.0),
                    'learning_rate': trial.suggest_float('learning_rate', 1e-4, 0.1, log=True),
                    'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                    'max_depth': trial.suggest_int('max_depth', 1, 9),
                }
                
                # Simple CV for optimization
                scores = []
                cv = splitter.split(X)
                
                for train_idx, val_idx in cv:
                    X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                    y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                    
                    model = xgb.XGBRegressor(**param)
                    model.fit(X_train, y_train)
                    preds = model.predict(X_val)
                    rmse = mean_squared_error(y_val, preds) ** 0.5
                    scores.append(rmse)
                    
                mean_rmse = sum(scores) / len(scores)
                # Log nested run for trial could be done, or just log best params later
                return mean_rmse

            study = optuna.create_study(direction='minimize', study_name=study_name)
            study.optimize(objective, n_trials=trial_count)
            
            logger.info("optimization_complete", best_params=study.best_params)
            experiment_manager.log_params(study.best_params)
            
            # Train final model
            # Determine training mode for logging
            training_mode = "warm_start" if warm_start and self.prev_model_path.exists() else "full"
            experiment_manager.log_params({"training_mode": training_mode})

            if warm_start and self.prev_model_path.exists():
                # Load previous model booster for incremental update
                prev_booster = xgb.Booster()
                prev_booster.load_model(str(self.prev_model_path))
                final_model = xgb.XGBRegressor(**study.best_params, xgb_model=prev_booster)
            else:
                final_model = xgb.XGBRegressor(**study.best_params)

            final_model.fit(X, y)
            
            self.save_model(final_model, "best_model.joblib")
            
            # Evaluate and log metrics
            metrics = self.evaluate(final_model, X, y)
            experiment_manager.log_metrics(metrics)
            
            # Log Artifact
            experiment_manager.log_artifact(str(self.model_dir / "best_model.joblib"))
            
            # Register Model
            # experiment_manager.register_model(f"runs:/{run.info.run_id}/best_model.joblib", "ApexFlow_LapTime_Predictor")
            
            return final_model

    def save_model(self, model: Any, name: str):
        path = self.model_dir / name
        joblib.dump(model, path)
        logger.info("model_saved", path=str(path))
        
    def evaluate(self, model, X, y):
        preds = model.predict(X)
        rmse = mean_squared_error(y, preds) ** 0.5
        mae = mean_absolute_error(y, preds)
        r2 = r2_score(y, preds)
        return {"rmse": rmse, "mae": mae, "r2": r2}

trainer = ModelTrainer()
