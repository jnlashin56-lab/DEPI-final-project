from backend.app.llm_client import generate_json
from backend.app.schemas import BookingAction

def handle_booking_chat(user_input: str) -> BookingAction:
    """
    Parses a user's chat message to extract a booking action.
    This replaces native tool-calling with a strict JSON structure.
    """
    prompt = f"""
You are an AI booking assistant for Egyptian cultural sites.
The user is talking to you to manage a booking.
Determine what action the user wants to take, and extract the necessary details into a JSON object.

Allowed actions:
- "check_availability": If the user is asking if a place is open/available at a certain time.
- "create_booking": If the user is explicitly asking to book or reserve tickets.
- "confirm_booking": If the user is confirming an existing pending booking.

The JSON MUST have this structure:
{{
  "action": "check_availability" | "create_booking" | "confirm_booking",
  "place_id": integer (if known, or 0 if unknown),
  "visit_date": "YYYY-MM-DD" (if mentioned),
  "visit_time": "HH:MM" (if mentioned),
  "visitor_name": string (if mentioned),
  "visitor_count": integer (if mentioned)
}}

If the user does not provide a detail, omit it or set it to null.

User message: "{user_input}"
"""

    response_data = generate_json(prompt, max_new_tokens=200)
    
    if "data" in response_data and isinstance(response_data["data"], dict):
        response_data = response_data["data"]
        
    return BookingAction(**response_data)
