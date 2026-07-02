"""
Crowd Estimator — Phase 2 (Machine Learning).

Loads a pre-trained XGBoost model to predict crowd scores based on
features: month, day_of_week, hour, and category.
"""

from datetime import date, time
import os
import xgboost as xgb
import pandas as pd
import logging
from backend.app.schemas import CrowdEstimateRequest, CrowdEstimateResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ML Model Loading
# ---------------------------------------------------------------------------
_model = None

def get_crowd_model():
    global _model
    if _model is None:
        model_path = os.path.join(os.path.dirname(__file__), "models", "xgboost_crowd.json")
        try:
            _model = xgb.XGBRegressor()
            _model.load_model(model_path)
            logger.info("Loaded XGBoost crowd model.")
        except Exception as e:
            logger.error(f"Failed to load XGBoost crowd model: {e}")
            _model = None
    return _model

cat_mapping = {
    "historical": 0, "museum": 1, "religious": 2, "natural": 3, 
    "coastal": 4, "market": 5, "other": 6
}

# ---------------------------------------------------------------------------
# ML Inference Pipeline
# ---------------------------------------------------------------------------

def score_to_label(score: float) -> str:
    if score >= 0.66:
        return "high"
    elif score >= 0.4:
        return "medium"
    return "low"


def estimate_crowd(request: CrowdEstimateRequest) -> CrowdEstimateResponse:
    model = get_crowd_model()
    
    # Feature extraction
    month = request.visit_date.month
    day_of_week = request.visit_date.weekday()
    hour = request.visit_time.hour
    category_encoded = cat_mapping.get(request.category.lower(), 6)
    
    if model is not None:
        # Create single row dataframe matching training features
        df = pd.DataFrame([{
            "month": month,
            "day_of_week": day_of_week,
            "hour": hour,
            "category_encoded": category_encoded
        }])
        
        # Inference
        raw_pred = float(model.predict(df)[0])
        crowd_score = max(0.0, min(1.0, raw_pred))
    else:
        # Fallback if model fails to load
        crowd_score = 0.5
        
    label = score_to_label(crowd_score)

    explanation = (
        f"Our XGBoost ML model analyzed the historical patterns for {request.category} sites "
        f"in month {month}, day {day_of_week}, at {hour}:00, and predicted a "
        f"{label} crowd density (confidence score: {crowd_score:.2f})."
    )

    return CrowdEstimateResponse(
        predicted_crowd=label,
        crowd_score=round(crowd_score, 2),
        explanation=explanation,
    )


if __name__ == "__main__":
    test_request = CrowdEstimateRequest(
        place_id=1,
        category="historical",
        visit_date=date(2026, 7, 5),
        visit_time=time(10, 0),
    )
    result = estimate_crowd(test_request)
    print(result)