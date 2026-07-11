import requests
import json

url = "http://127.0.0.1:8000/chat/booking"
payload = {
    "user_input": "Book Luxor Temple for 2 people tomorrow at 10am. My name is Yousef Ahmed.",
    "context": [
        {"role": "assistant", "content": "Hi! I can help you book tickets for KV7. How many people are going, and what time would you like to visit?"}
    ],
    "place_id": 5
}
try:
    res = requests.post(url, json=payload)
    print("STATUS:", res.status_code)
    print("RESPONSE:", res.text)
except Exception as e:
    print("ERROR:", e)
