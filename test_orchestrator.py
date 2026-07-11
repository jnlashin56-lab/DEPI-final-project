import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.orchestrator import run_orchestration
from backend.app.db import pool
from backend.app.retrieval import get_model
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    try:
        pool.open()
        get_model()
        response = run_orchestration("I want a plan for 3 days in Cairo and I have 4000 le")
        for stop in response.itinerary:
            print(f"Place: {stop.name}, Day: {stop.day}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        pool.close()
