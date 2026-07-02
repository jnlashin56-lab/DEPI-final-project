import datetime
from typing import List

from backend.app.schemas import (
    RecommendationRequest, 
    RecommendationResponse, 
    Candidate,
    ScoredCandidate,
    ItineraryStop
)

from backend.app.agents.preference_agent import parse_user_preferences
from backend.app.agents.recommender_agent import rank_and_select_candidates
from backend.app.agents.story_generator import generate_story
from backend.app.crowd import estimate_crowd
from backend.app.schemas import CrowdEstimateRequest
from backend.app.retrieval import search_places

def get_real_candidates(query: str, category: str | None = None) -> List[Candidate]:
    """Wraps retrieval to map DB rows to the Candidate schema."""
    results = search_places(query_text=query, category=category, limit=30)
    candidates = []
    for row in results:
        row_dict = dict(row)
        if "id" in row_dict:
            row_dict["place_id"] = row_dict.pop("id")
        candidates.append(Candidate(**row_dict))
    return candidates

def score_candidates(
    candidates: List[Candidate], visit_date: datetime.date, visit_time: datetime.time
) -> List[ScoredCandidate]:
    """Applies the rule-based crowd estimator to each candidate."""
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

def run_orchestration(user_input: str) -> RecommendationResponse:
    """
    Executes the full LLM agent pipeline:
    Preference -> Retrieval -> Crowd -> Recommender -> Story
    """
    # 1. Preference Agent
    request = parse_user_preferences(user_input)
    
    # Fill defaults if missing
    visit_date = request.visit_date or datetime.date.today()
    visit_time = request.visit_time or datetime.time(10, 0)
    
    # 2. Retrieval
    # If they asked for a specific interest, maybe we can use it as a category.
    # For now we'll rely on semantic search for the main query.
    candidates = get_real_candidates(request.query)
    
    # 3. Crowd Estimator
    scored = score_candidates(candidates, visit_date, visit_time)
    
    # 4. Recommender Agent
    itinerary = rank_and_select_candidates(scored, request, max_stops=3)
    
    # 5. Story Generator
    for stop in itinerary:
        story = generate_story(stop)
        stop.story = story
        
    return RecommendationResponse(itinerary=itinerary)
