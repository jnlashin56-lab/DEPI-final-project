from pydantic import BaseModel, Field

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
