"""
Shared data contracts for the Cultural Recommender backend.

Both you (crowd/booking/schemas/mock_recommender) and your teammate
(embeddings/retrieval) import from this file. It defines the exact
shape of data passed between every stage of the pipeline, so changes
here should be small, and pushed/communicated quickly since both of
you depend on it.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, time

# ---------------------------------------------------------------------------
# Retrieval output — what your teammate's retrieval.py returns
# You consume this as input to crowd.py and mock_recommender.py
# ---------------------------------------------------------------------------

class Candidate(BaseModel):
    """A single place returned by semantic retrieval, before crowd/ranking."""
    place_id: int
    name: str
    name_ar: Optional[str] = None
    category: str
    category_ar: Optional[str] = None
    description: Optional[str] = None
    description_ar: Optional[str] = None
    price_egp: Optional[float] = None
    similarity: float = Field(ge=0.0, le=1.0)


class RetrievalResponse(BaseModel):
    """What GET /retrieval returns — the top ~30 candidates."""
    candidates: List[Candidate]


# ---------------------------------------------------------------------------
# Crowd Estimator — your module
# ---------------------------------------------------------------------------

class CrowdEstimateRequest(BaseModel):
    place_id: int
    category: str
    visit_date: date
    visit_time: time


class CrowdEstimateResponse(BaseModel):
    predicted_crowd: str  # "low" | "medium" | "high"
    crowd_score: float = Field(ge=0.0, le=1.0)
    explanation: str


# A candidate after crowd scoring has been attached — this is what flows
# into the Recommender Agent per the pipeline (step 5 -> step 6).
class ScoredCandidate(Candidate):
    predicted_crowd: str
    crowd_score: float = Field(ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Recommendation — mock_recommender.py (later: recommender.py, built together)
# ---------------------------------------------------------------------------

class RecommendationRequest(BaseModel):
    query: str
    city: Optional[str] = None
    budget_egp: Optional[float] = None
    interests: Optional[List[str]] = None
    available_hours: Optional[float] = None
    crowd_tolerance: Optional[str] = None  # "low" | "medium" | "high"
    visit_date: Optional[date] = None
    visit_time: Optional[time] = None


class ItineraryStop(ScoredCandidate):
    story: Optional[str] = None  # filled in later by the Story Generator


class RecommendationResponse(BaseModel):
    itinerary: List[ItineraryStop]


# ---------------------------------------------------------------------------
# Booking — bookings.py
# ---------------------------------------------------------------------------

class BookingRequest(BaseModel):
    place_id: int
    visitor_name: str
    visitor_count: int = Field(ge=1)
    visit_date: date
    visit_time: time


class BookingResponse(BaseModel):
    booking_id: int
    status: str  # "confirmed" | "pending" | "failed"
    place_id: int
    visitor_name: str
    visitor_count: int
    visit_date: date
    visit_time: time
    total_price_egp: Optional[float] = None
    message: Optional[str] = None


# The Booking Agent (LLM) dispatches actions as JSON objects rather than
# native tool-calling, per the plan. bookings.py exposes functions that
# these actions map onto — e.g. action="check_availability" -> check_availability().
class BookingAction(BaseModel):
    action: str  # "check_availability" | "create_booking" | "confirm_booking"
    place_id: int
    visit_date: Optional[date] = None
    visit_time: Optional[time] = None
    visitor_name: Optional[str] = None
    visitor_count: Optional[int] = None