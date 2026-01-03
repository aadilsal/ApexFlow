import joblib
import xgboost as xgb
from pathlib import Path

model_path = Path("models/best_model.joblib")
model = joblib.load(model_path)

if hasattr(model, "feature_names_in_"):
    features = model.feature_names_in_
else:
    try:
        features = model.get_booster().feature_names
    except:
        features = ["Unknown"]

print("---BEGIN FEATURES---")
for f in features:
    print(f)
print("---END FEATURES---")

if hasattr(model, "get_params"):
    print(f"Enable Categorical: {model.get_params().get('enable_categorical', False)}")
