import datetime
import time as _time
import logging
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

logger = logging.getLogger(__name__)

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
    """Applies the XGBoost crowd estimator to each candidate."""
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
    
    Logs latency at each stage for evaluation.
    """
    latency = {}
    t0 = _time.perf_counter()
    
    # 1. Preference Agent (LLM)
    t1 = _time.perf_counter()
    request = parse_user_preferences(user_input)
    latency["preference_agent_ms"] = round((_time.perf_counter() - t1) * 1000)
    
    # Fill defaults if missing
    visit_date = request.visit_date or datetime.date.today()
    visit_time = request.visit_time or datetime.time(10, 0)
    
    # 2. Retrieval (pgvector)
    t2 = _time.perf_counter()
    candidates = get_real_candidates(request.query)
    latency["retrieval_ms"] = round((_time.perf_counter() - t2) * 1000)
    
    # 3. Crowd Estimator (XGBoost)
    t3 = _time.perf_counter()
    scored = score_candidates(candidates, visit_date, visit_time)
    latency["crowd_estimator_ms"] = round((_time.perf_counter() - t3) * 1000)
    
    # 4. Recommender Agent (LLM)
    t4 = _time.perf_counter()
    itinerary = rank_and_select_candidates(scored, request, max_stops=3)
    latency["recommender_agent_ms"] = round((_time.perf_counter() - t4) * 1000)
    
    # 5. Story Generator (LLM)
    t5 = _time.perf_counter()
    for stop in itinerary:
        story = generate_story(stop)
        stop.story = story
    latency["story_generator_ms"] = round((_time.perf_counter() - t5) * 1000)
    
    latency["total_e2e_ms"] = round((_time.perf_counter() - t0) * 1000)
    
    logger.info(f"Pipeline latency: {latency}")
    
    # Store latency for the evaluation runner to access
    run_orchestration._last_latency = latency
        
    return RecommendationResponse(itinerary=itinerary)
