from datetime import date, time
from typing import List

from backend.app.schemas import (
    Candidate,
    CrowdEstimateRequest,
    ScoredCandidate,
    RecommendationRequest,
    RecommendationResponse,
    ItineraryStop,
)
from backend.app.crowd import estimate_crowd


# ---------------------------------------------------------------------------
# Fake candidates — stand-in for backend/app/retrieval.py's real output.
# Matches the exact contract shape you and your teammate agreed on.
# ---------------------------------------------------------------------------

def get_fake_candidates() -> List[Candidate]:
    return [
        Candidate(
            place_id=1,
            name="Karnak Temple",
            name_ar="معبد الكرنك",
            category="historical",
            category_ar="تاريخي",
            description="A vast temple complex built over centuries.",
            description_ar="مجمع معابد ضخم بُني على مدى قرون.",
            price_egp=450.0,
            similarity=0.91,
        ),
        Candidate(
            place_id=2,
            name="Luxor Museum",
            name_ar="متحف الأقصر",
            category="museum",
            category_ar="متحف",
            description="A quiet museum with well-preserved artifacts.",
            description_ar="متحف هادئ يضم قطعًا أثرية محفوظة جيدًا.",
            price_egp=140.0,
            similarity=0.85,
        ),
        Candidate(
            place_id=3,
            name="Fraser Tombs",
            name_ar="مقابر فريزر",
            category="historical",
            category_ar="تاريخي",
            description="Lesser-known tombs, rarely crowded.",
            description_ar="مقابر أقل شهرة ونادرًا ما تكون مزدحمة.",
            price_egp=200.0,
            similarity=0.84,
        ),
    ]


# ---------------------------------------------------------------------------
# Attach crowd scores to each candidate using your real crowd.py logic.
# ---------------------------------------------------------------------------

def score_candidates(
    candidates: List[Candidate], visit_date: date, visit_time: time
) -> List[ScoredCandidate]:
    scored = []
    for c in candidates:
        crowd_result = estimate_crowd(
            CrowdEstimateRequest(
                place_id=c.place_id,
                category=c.category,
                visit_date=visit_date,
                visit_time=visit_time,
            )
        )
        scored.append(
            ScoredCandidate(
                **c.model_dump(),
                predicted_crowd=crowd_result.predicted_crowd,
                crowd_score=crowd_result.crowd_score,
            )
        )
    return scored


# ---------------------------------------------------------------------------
# Simple ranking: sort by similarity first, filter by budget if given.
# This is a placeholder for the real Recommender Agent (LLM) that will
# eventually replace this function, per the plan.
# ---------------------------------------------------------------------------

def rank_and_select(
    scored: List[ScoredCandidate], request: RecommendationRequest, max_stops: int = 3
) -> List[ItineraryStop]:
    filtered = scored
    if request.budget_egp is not None:
        filtered = [
            c for c in filtered
            if c.price_egp is None or c.price_egp <= request.budget_egp
        ]

    ranked = sorted(filtered, key=lambda c: c.similarity, reverse=True)
    top = ranked[:max_stops]

    return [ItineraryStop(**c.model_dump(), story=None) for c in top]


# ---------------------------------------------------------------------------
# The mock recommendation endpoint's core logic.
# ---------------------------------------------------------------------------

def get_mock_recommendation(request: RecommendationRequest) -> RecommendationResponse:
    candidates = get_fake_candidates()

    visit_date = request.visit_date or date.today()
    visit_time = request.visit_time or time(10, 0)

    scored = score_candidates(candidates, visit_date, visit_time)
    itinerary = rank_and_select(scored, request)

    return RecommendationResponse(itinerary=itinerary)


# ---------------------------------------------------------------------------
# Quick manual test — run this file directly:
#   python -m backend.app.mock_recommender
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_request = RecommendationRequest(
        query="quiet ancient temples in Luxor",
        city="Luxor",
        budget_egp=300,
        visit_date=date(2026, 7, 5),
        visit_time=time(10, 0),
    )
    response = get_mock_recommendation(test_request)
    for stop in response.itinerary:
        print(stop)