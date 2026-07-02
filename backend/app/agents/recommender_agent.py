from typing import List
from backend.app.llm_client import generate_json
from backend.app.schemas import ScoredCandidate, RecommendationRequest, ItineraryStop

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

Candidates:
{candidates_json}

Instructions:
1. Select up to {max_stops} places that best fit the user's preferences.
2. Consider the budget and crowd tolerance (if specified).
3. Order them logically for an itinerary.
4. Output a JSON array containing ONLY the selected `place_id`s in order.

Example output:
[10, 45, 123]
"""
    
    response_data = generate_json(prompt, max_new_tokens=200)
    
    selected_ids = []
    if isinstance(response_data, dict):
        # Depending on how json_repair formats the list, extract it
        if "data" in response_data:
            selected_ids = response_data["data"]
        else:
            # Maybe it output {"place_ids": [1,2,3]}
            for key, val in response_data.items():
                if isinstance(val, list):
                    selected_ids = val
                    break
    elif isinstance(response_data, list):
        selected_ids = response_data
        
    # Ensure they are integers
    try:
        selected_ids = [int(i) for i in selected_ids]
    except (ValueError, TypeError):
        # Fallback if the LLM output something weird
        selected_ids = [c.place_id for c in candidates[:max_stops]]
        
    # Filter and order candidates based on the LLM's selection
    candidate_dict = {c.place_id: c for c in candidates}
    
    itinerary = []
    for pid in selected_ids:
        if pid in candidate_dict:
            c = candidate_dict[pid]
            itinerary.append(ItineraryStop(**c.model_dump(), story=None))
            
    # Fallback if the LLM failed to select anything valid
    if not itinerary:
        itinerary = [ItineraryStop(**c.model_dump(), story=None) for c in candidates[:max_stops]]
        
    return itinerary[:max_stops]
