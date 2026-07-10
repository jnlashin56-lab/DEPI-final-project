import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.llm_client import generate_text, generate_json

print("Testing generate_text...")
try:
    text = generate_text("Tell me a 1-sentence story about Luxor Temple.")
    print(f"TEXT OUTPUT: {repr(text)}")
except Exception as e:
    print(f"TEXT ERROR: {e}")

print("\nTesting generate_json...")
try:
    data = generate_json('Extract place_id 5 and day 1 into this JSON: {"place_id": int, "day": int}')
    print(f"JSON OUTPUT: {data}")
except Exception as e:
    print(f"JSON ERROR: {e}")
