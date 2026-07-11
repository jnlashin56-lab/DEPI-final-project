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
# Retrieval API Schemas
# ---------------------------------------------------------------------------

class RecommendRequest(BaseModel):
    user_input: str

from typing import List, Dict, Any, Optional

class BookingChatRequest(BaseModel):
    user_input: str

class SearchRequest(BaseModel):
    query: str
    category: str | None = None
    limit: int = Field(default=10, ge=1, le=50)

class PlaceResult(BaseModel):
    id: int
    source_place_id: int | None
    name: str
    name_ar: str | None
    category: str | None
    category_ar: str | None
    description: str | None
    description_ar: str | None
    latitude: float | None
    longitude: float | None
    price_egp: float | None
    similarity: float

class SearchResponse(BaseModel):
    query: str
    results: list[PlaceResult]
    count: int

class HealthResponse(BaseModel):
    status: str
    database: bool
    embedding_model: str
    places_count: int
    places_with_embeddings: int

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
    num_days: Optional[int] = None


class ItineraryStop(ScoredCandidate):
    story: Optional[str] = None  # filled in later by the Story Generator
    day: int = 1


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
    visit_date: Optional[str] = None
    visit_time: Optional[str] = None
    visitor_name: Optional[str] = None
    visitor_count: Optional[int] = None


# ---------------------------------------------------------------------------
# Admin Panel Schemas
# ---------------------------------------------------------------------------

class AdminLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Places admin
class PlaceCreate(BaseModel):
    name: str
    name_ar: Optional[str] = None
    category: Optional[str] = None
    category_ar: Optional[str] = None
    description: Optional[str] = None
    description_ar: Optional[str] = None
    price_egp: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class PlaceUpdate(PlaceCreate):
    pass

class PlaceAdmin(BaseModel):
    id: int
    source_place_id: Optional[int] = None
    name: str
    name_ar: Optional[str] = None
    category: Optional[str] = None
    category_ar: Optional[str] = None
    description: Optional[str] = None
    description_ar: Optional[str] = None
    price_egp: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    has_embedding: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class PlaceListResponse(BaseModel):
    places: List[PlaceAdmin]
    total: int
    page: int
    page_size: int

# Ticket prices admin
class TicketPriceAdmin(BaseModel):
    id: int
    site_name: str
    governorate: Optional[str] = None
    heritage_type: Optional[str] = None
    egyptian_egp: Optional[float] = None
    egyptian_student_egp: Optional[float] = None
    foreign_egp: Optional[float] = None
    foreign_student_egp: Optional[float] = None
    visiting_hours: Optional[str] = None

class TicketPriceUpdate(BaseModel):
    egyptian_egp: Optional[float] = None
    egyptian_student_egp: Optional[float] = None
    foreign_egp: Optional[float] = None
    foreign_student_egp: Optional[float] = None
    visiting_hours: Optional[str] = None

# Bookings admin
class BookingAdmin(BaseModel):
    id: int
    place_id: int
    place_name: Optional[str] = None
    visitor_name: str
    visitor_type: str
    visitor_count: int
    visit_date: date
    visit_time: Optional[time] = None
    status: str
    total_price_egp: Optional[float] = None
    confirmation_code: str
    created_at: Optional[str] = None

# Crowd profiles admin
class CrowdProfileAdmin(BaseModel):
    place_id: int
    place_name: Optional[str] = None
    base_crowd_level: str
    peak_hours: Optional[List[str]] = None
    peak_season_months: Optional[List[int]] = None
    is_outdoor: bool = True
    notes: Optional[str] = None

class CrowdProfileUpdate(BaseModel):
    base_crowd_level: str
    peak_hours: Optional[List[str]] = None
    peak_season_months: Optional[List[int]] = None
    is_outdoor: Optional[bool] = None
    notes: Optional[str] = None

# Analytics
class AnalyticsResponse(BaseModel):
    total_bookings: int
    total_revenue: float
    active_places: int
    places_with_embeddings: int
    top_booked_places: List[Dict[str, Any]]
    bookings_by_status: Dict[str, int]
    recent_bookings: List[Dict[str, Any]]

