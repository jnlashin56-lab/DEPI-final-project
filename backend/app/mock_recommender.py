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
from backend.app.retrieval import search_places


# ---------------------------------------------------------------------------
# Real retrieval integration
# ---------------------------------------------------------------------------

def get_real_candidates(query: str) -> List[Candidate]:
    results = search_places(query_text=query, limit=30)
    candidates = []
    for row in results:
        row_dict = dict(row)
        # Map our DB 'id' to the schema's 'place_id'
        if "id" in row_dict:
            row_dict["place_id"] = row_dict.pop("id")
        candidates.append(Candidate(**row_dict))
    return candidates


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
    candidates = get_real_candidates(request.query)

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
    from backend.app.db import pool
    pool.open()
    try:
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
    finally:
        pool.close()