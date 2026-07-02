from typing import Any
import datetime
from backend.app.llm_client import generate_json
from backend.app.schemas import RecommendationRequest

def parse_user_preferences(user_input: str) -> RecommendationRequest:
    """
    Uses the LLM to extract structured search filters from free-text user input.
    """
    today = datetime.date.today().isoformat()
    
    prompt = f"""
You are an expert travel assistant. Extract the user's travel preferences from their input into a structured JSON object.
Today's date is {today}.

Extract the following fields (if mentioned, otherwise leave them null):
- "query": A summary of what they are looking for (e.g. "ancient temples in Luxor")
- "city": The specific city they want to visit (e.g. "Luxor", "Aswan", "Cairo").
- "budget_egp": The maximum budget in EGP as a number.
- "interests": A list of strings representing their interests (e.g. ["history", "museums", "nature"]).
- "available_hours": A number representing how many hours they have available.
- "crowd_tolerance": Must be exactly one of: "low", "medium", "high". Default to null if not mentioned.
- "visit_date": A date in YYYY-MM-DD format if they mention when they are going.
- "visit_time": A time in HH:MM format if they mention a specific time of day.

User input: "{user_input}"
"""
    response_data = generate_json(prompt, max_new_tokens=300)
    
    # Handle the fact that json_repair might wrap the response in {"data": ...} or similar
    if "data" in response_data and isinstance(response_data["data"], dict):
        response_data = response_data["data"]
        
    # Provide a default query if none was extracted, as it is required by the schema
    if "query" not in response_data or not response_data["query"]:
         response_data["query"] = user_input
         
    return RecommendationRequest(**response_data)
