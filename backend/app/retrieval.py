import os
import threading
from sentence_transformers import SentenceTransformer
from backend.app.db import get_connection

# Lazy model loading
_model = None
_model_lock = threading.Lock()

def get_model_name() -> str:
    return os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                model_name = get_model_name()
                _model = SentenceTransformer(model_name)
    return _model

def encode_query(text: str) -> list[float]:
    """
    Wrap the query with the E5 prefix and encode it.
    Returns a Python list of floats.
    """
    model = get_model()
    # Using 'query: ' for symmetric search as we used 'query: ' for document embeddings.
    # We can improve this pattern later.
    prefixed_text = f"query: {text}"
    embedding = model.encode([prefixed_text], normalize_embeddings=True)[0]
    return embedding.tolist()

def search_places(query_text: str, category: str | None = None, limit: int = 10) -> list[dict]:
    query_vector = encode_query(query_text)
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            if category:
                sql = """
                    SELECT id, source_place_id, name, name_ar, category, category_ar,
                           description, description_ar, latitude, longitude, price_egp,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM places
                    WHERE embedding IS NOT NULL
                      AND lower(category) = lower(%s)
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """
                cur.execute(sql, (query_vector, category, query_vector, limit))
            else:
                sql = """
                    SELECT id, source_place_id, name, name_ar, category, category_ar,
                           description, description_ar, latitude, longitude, price_egp,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM places
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """
                cur.execute(sql, (query_vector, query_vector, limit))
                
            return cur.fetchall()
