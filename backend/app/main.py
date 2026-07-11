from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

from backend.app.db import pool, get_connection
from backend.app.schemas import (
    SearchRequest, SearchResponse, HealthResponse, PlaceResult,
    RecommendRequest, RecommendationResponse, BookingChatRequest
)
from backend.app.retrieval import get_model, get_model_name, search_places
from backend.app.orchestrator import run_orchestration
from backend.app.agents.booking_agent import handle_booking_chat
from backend.app.bookings import dispatch_action
from backend.app.admin import router as admin_router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up FastAPI application...")
    logger.info("Opening database connection pool...")
    pool.open()
    
    logger.info(f"Loading embedding model: {get_model_name()}...")
    logger.info("Model loaded successfully.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI application...")
    logger.info("Closing database connection pool...")
    pool.close()

app = FastAPI(title="Cultural Recommender API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)

@app.get("/health", response_model=HealthResponse)
def health_check():
    db_ok = False
    places_count = 0
    places_with_embeddings = 0
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Simple check
                cur.execute("SELECT 1")
                db_ok = True
                
                # Get counts
                cur.execute("SELECT COUNT(*) FROM places")
                places_count = cur.fetchone()["count"]
                
                cur.execute("SELECT COUNT(*) FROM places WHERE embedding IS NOT NULL")
                places_with_embeddings = cur.fetchone()["count"]
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        database=db_ok,
        embedding_model=get_model_name(),
        places_count=places_count,
        places_with_embeddings=places_with_embeddings
    )

@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    try:
        results = search_places(
            query_text=request.query,
            category=request.category,
            limit=request.limit
        )
        
        # Convert DB dicts to Pydantic models
        place_results = [PlaceResult(**row) for row in results]
        
        return SearchResponse(
            query=request.query,
            results=place_results,
            count=len(place_results)
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/recommend", response_model=RecommendationResponse)
def recommend_itinerary(request: RecommendRequest):
    try:
        # Runs the full agent pipeline
        response = run_orchestration(request.user_input)
        return response
    except Exception as e:
        logger.error(f"Recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/booking")
def chat_booking(request: BookingChatRequest):
    try:
        action = handle_booking_chat(request.user_input)
        result = dispatch_action(action)
        return {"action_taken": action.model_dump(), "result": result}
    except Exception as e:
        logger.error(f"Booking chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
