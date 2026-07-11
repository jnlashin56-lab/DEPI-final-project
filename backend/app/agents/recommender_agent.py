from typing import List
import logging
from backend.app.llm_client import generate_json
from backend.app.schemas import ScoredCandidate, RecommendationRequest, ItineraryStop

logger = logging.getLogger(__name__)

def rank_and_select_candidates(
    candidates: List[ScoredCandidate], 
    request: RecommendationRequest, 
    max_stops: int = 3
) -> List[ItineraryStop]:
    """
    Uses the LLM to select and order the best 3-5 places from a shortlist of candidates.
    """
    
    # Format candidates for the prompt
    candidates_json = []
    for c in candidates:
        candidates_json.append({
            "place_id": c.place_id,
            "name": c.name,
            "category": c.category,
            "price_egp": c.price_egp,
            "similarity_score": round(c.similarity, 2),
            "predicted_crowd": c.predicted_crowd,
            "description": c.description
        })
        
    prompt = f"""
You are an expert Egyptian tour guide. You have a list of candidate places matching the user's query.
Your job is to select the best {max_stops} stops for their itinerary.

User Preferences:
- Query: {request.query}
- City: {request.city}
- Budget (EGP): {request.budget_egp}
- Interests: {request.interests}
- Crowd Tolerance: {request.crowd_tolerance}
- Available Hours: {request.available_hours}
- Days: {request.num_days or 1}

Candidates:
{candidates_json}

Instructions:
1. Select up to {max_stops} places that best fit the user's preferences.
2. Consider the budget and crowd tolerance (if specified).
3. Order them logically for an itinerary.
4. Output a JSON array containing objects with `place_id` and `day` (day 1 to {request.num_days or 1}).

Example output:
[
  {{"place_id": 10, "day": 1}},
  {{"place_id": 45, "day": 1}},
  {{"place_id": 123, "day": 2}}
]
"""

    
    response_data = generate_json(prompt, max_new_tokens=500)
    
    logger.info(f"Recommender LLM response: {response_data}")
    
    selected_items = []
    if isinstance(response_data, dict):
        # Depending on how json_repair formats the list, extract it
        if "data" in response_data:
            selected_items = response_data["data"]
        else:
            # Maybe it output {"places": [...]}
            for key, val in response_data.items():
                if isinstance(val, list):
                    selected_items = val
                    break
    elif isinstance(response_data, list):
        selected_items = response_data
        
    candidate_dict = {c.place_id: c for c in candidates}
    itinerary = []
    
    try:
        for item in selected_items:
            if isinstance(item, dict) and "place_id" in item:
                pid = int(item["place_id"])
                day = int(item.get("day", 1))
                if pid in candidate_dict:
                    c = candidate_dict[pid]
                    itinerary.append(ItineraryStop(**c.model_dump(), story=None, day=day))
            elif isinstance(item, int) or isinstance(item, str):
                pid = int(item)
                if pid in candidate_dict:
                    c = candidate_dict[pid]
                    itinerary.append(ItineraryStop(**c.model_dump(), story=None, day=1))
    except (ValueError, TypeError):
        pass
            
    # Fallback if the LLM failed to select anything valid
    if not itinerary:
        itinerary = [ItineraryStop(**c.model_dump(), story=None, day=1) for c in candidates[:max_stops]]

        
    return itinerary[:max_stops]
