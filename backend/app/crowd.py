"""
Crowd Estimator — Phase 1 (rule-based, no ML).

Combines a base crowd level per category with three multipliers
(time of day, day of week, season) into a single 0-1 crowd_score,
then buckets that score into "low" / "medium" / "high".

This is intentionally simple and fully explainable — every number
here is a hand-picked constant you can point to and justify in a
defense, not a learned weight.
"""

from datetime import date, time
from backend.app.schemas import CrowdEstimateRequest, CrowdEstimateResponse


# ---------------------------------------------------------------------------
# Step 1: base crowd level per category
# Tune these as you learn more about your actual dataset's categories.
# ---------------------------------------------------------------------------

BASE_CROWD_BY_CATEGORY = {
    "historical": 0.6,   # major ancient sites — generally busy
    "museum": 0.4,
    "religious": 0.5,
    "natural": 0.3,      # desert/nature sites — generally quieter
    "coastal": 0.35,
    "market": 0.55,
}
DEFAULT_BASE_CROWD = 0.4  # fallback for any category not listed above


def get_base_crowd(category: str) -> float:
    return BASE_CROWD_BY_CATEGORY.get(category.lower(), DEFAULT_BASE_CROWD)


# ---------------------------------------------------------------------------
# Step 2: time-of-day multiplier
# Midday is busiest; early morning and late afternoon are quieter.
# ---------------------------------------------------------------------------

def time_of_day_multiplier(visit_time: time) -> float:
    hour = visit_time.hour
    if 11 <= hour < 15:
        return 1.3   # midday peak
    elif 9 <= hour < 11 or 15 <= hour < 17:
        return 1.0   # normal
    else:
        return 0.7   # early morning / late afternoon — quieter


# ---------------------------------------------------------------------------
# Step 3: day-of-week multiplier
# Friday/Saturday are the tourist-heavy weekend in Egypt.
# ---------------------------------------------------------------------------

def day_of_week_multiplier(visit_date: date) -> float:
    weekday = visit_date.weekday()  # Monday=0 ... Sunday=6
    if weekday in (4, 5):  # Friday, Saturday
        return 1.2
    return 1.0


# ---------------------------------------------------------------------------
# Step 4: season multiplier
# Oct-Apr is Egypt's tourist season -> busier for most sites.
# Summer is quieter for desert/outdoor sites, busier for coastal ones.
# ---------------------------------------------------------------------------

def season_multiplier(visit_date: date, category: str) -> float:
    month = visit_date.month
    is_tourist_season = month in (10, 11, 12, 1, 2, 3, 4)

    if category.lower() == "coastal":
        # coastal sites flip: busier in summer, quieter in tourist season
        return 1.2 if not is_tourist_season else 0.9

    return 1.3 if is_tourist_season else 0.8


# ---------------------------------------------------------------------------
# Step 5: combine into a score, then bucket into low/medium/high
# ---------------------------------------------------------------------------

def score_to_label(score: float) -> str:
    if score >= 0.66:
        return "high"
    elif score >= 0.4:
        return "medium"
    return "low"


def estimate_crowd(request: CrowdEstimateRequest) -> CrowdEstimateResponse:
    base = get_base_crowd(request.category)
    tod_mult = time_of_day_multiplier(request.visit_time)
    dow_mult = day_of_week_multiplier(request.visit_date)
    season_mult = season_multiplier(request.visit_date, request.category)

    raw_score = base * tod_mult * dow_mult * season_mult
    crowd_score = max(0.0, min(1.0, raw_score))  # clamp to [0, 1]

    label = score_to_label(crowd_score)

    explanation = (
        f"{request.category.capitalize()} sites have a base crowd level of "
        f"{base:.2f}. Visiting at {request.visit_time.strftime('%H:%M')} "
        f"({'peak' if tod_mult > 1 else 'off-peak'} hours) and on a "
        f"{'weekend' if dow_mult > 1 else 'weekday'} during "
        f"{'tourist' if season_mult > 1 and request.category.lower() != 'coastal' else 'off-peak'} "
        f"season results in a predicted crowd level of {label}."
    )

    return CrowdEstimateResponse(
        predicted_crowd=label,
        crowd_score=round(crowd_score, 2),
        explanation=explanation,
    )


# ---------------------------------------------------------------------------
# Quick manual test — run this file directly to check it works,
# without needing main.py or a running server:
#   python -m backend.app.crowd
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_request = CrowdEstimateRequest(
        place_id=1,
        category="historical",
        visit_date=date(2026, 7, 5),
        visit_time=time(10, 0),
    )
    result = estimate_crowd(test_request)
    print(result)