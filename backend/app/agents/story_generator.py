from backend.app.llm_client import generate_text
from backend.app.schemas import ItineraryStop

def generate_story(stop: ItineraryStop) -> str:
    """
    Generates a culturally rich and engaging narrative for a specific place.
    """
    prompt = f"""
You are an expert Egyptian storyteller and tour guide.
Write a short, engaging, and culturally rich narrative about the following place for a visitor's itinerary.
It should be maximum 3-4 sentences long. Do not use generic corporate language; make it sound like a passionate local guide sharing a secret.

Place Name: {stop.name}
Category: {stop.category}
Description: {stop.description}

Story:
"""
    
    # We use a slightly higher temperature for more creative storytelling
    story = generate_text(prompt, max_new_tokens=200, temperature=0.8)
    return story
