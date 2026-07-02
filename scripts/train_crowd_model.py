import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import json

print("Generating synthetic dataset...")
np.random.seed(42)

NUM_SAMPLES = 10000

# 1. Generate random inputs
months = np.random.randint(1, 13, NUM_SAMPLES)
days_of_week = np.random.randint(0, 7, NUM_SAMPLES) # 0=Mon, 6=Sun
hours = np.random.randint(6, 22, NUM_SAMPLES)       # Visiting hours 6 AM to 9 PM
categories = np.random.choice(["historical", "museum", "religious", "natural", "coastal", "market", "other"], NUM_SAMPLES)

# Encode categories manually to avoid needing a scikit-learn encoder artifact
cat_mapping = {
    "historical": 0, "museum": 1, "religious": 2, "natural": 3, 
    "coastal": 4, "market": 5, "other": 6
}
categories_encoded = np.array([cat_mapping[c] for c in categories])

# 2. Apply our existing logic to generate the "ground truth" target
BASE_CROWD = {
    "historical": 0.6, "museum": 0.4, "religious": 0.5,
    "natural": 0.3, "coastal": 0.35, "market": 0.55, "other": 0.4
}

def calculate_target(row):
    base = BASE_CROWD[row["category"]]
    
    # Time multiplier
    hour = row["hour"]
    if 11 <= hour < 15: tod = 1.3
    elif 9 <= hour < 11 or 15 <= hour < 17: tod = 1.0
    else: tod = 0.7
    
    # Day multiplier
    dow = row["day_of_week"]
    dow_mult = 1.2 if dow in (4, 5) else 1.0 # Fri, Sat
    
    # Season multiplier
    month = row["month"]
    is_tourist_season = month in (10, 11, 12, 1, 2, 3, 4)
    if row["category"] == "coastal":
        season_mult = 1.2 if not is_tourist_season else 0.9
    else:
        season_mult = 1.3 if is_tourist_season else 0.8
        
    score = base * tod * dow_mult * season_mult
    
    # Add a tiny bit of random noise to make the ML model work for its generalizations
    noise = np.random.normal(0, 0.05)
    
    return max(0.0, min(1.0, score + noise))

df = pd.DataFrame({
    "month": months,
    "day_of_week": days_of_week,
    "hour": hours,
    "category": categories,
    "category_encoded": categories_encoded
})

df["target_score"] = df.apply(calculate_target, axis=1)

X = df[["month", "day_of_week", "hour", "category_encoded"]]
y = df["target_score"]

print("Training XGBoost Regressor...")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = xgb.XGBRegressor(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=5,
    random_state=42
)

model.fit(X_train, y_train)

# Evaluate
preds = model.predict(X_test)
mse = mean_squared_error(y_test, preds)
r2 = r2_score(y_test, preds)
print(f"Model trained! MSE: {mse:.4f} | R2 Score: {r2:.4f}")

# Save the model
model_path = "backend/app/models/xgboost_crowd.json"
model.save_model(model_path)
print(f"Model saved to {model_path}")
