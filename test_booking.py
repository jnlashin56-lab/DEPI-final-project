import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.agents.booking_agent import handle_booking_chat
from backend.app.bookings import dispatch_action
from backend.app.db import pool

if __name__ == "__main__":
    pool.open()
    try:
        user_input = """Place: Karnak Temple Complex.
Chat History:
Assistant: Hi! I can help you book tickets for Karnak Temple Complex. How many people are going, and what time would you like to visit?
User: 4 people , 2 pm
Assistant: Please provide your: name, date.
User: yousef , 20/7/2026"""
        
        print("Extracting action...")
        action = handle_booking_chat(user_input)
        print("Extracted Action:", action.model_dump())
        
        print("Dispatching...")
        result = dispatch_action(action)
        print("Result:", result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        pool.close()
