import os
import time
from typing import Any
import psycopg
from psycopg.rows import dict_row
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

DEFAULT_DATABASE_URL = (
    "postgresql://cultural_user:cultural_password@localhost:5432/cultural_recommender"
)

def database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

def build_embedding_text(row: dict[str, Any]) -> str:
    """
    Build bilingual text for embedding from a place row.
    E5 requires the 'query: ' prefix for symmetric search.
    """
    parts = []
    
    # English parts
    if row.get("name"):
        parts.append(row["name"])
    if row.get("category"):
        parts.append(row["category"])
    if row.get("description"):
        parts.append(row["description"])
        
    # Arabic parts
    if row.get("name_ar"):
        parts.append(row["name_ar"])
    if row.get("category_ar"):
        parts.append(row["category_ar"])
    if row.get("description_ar"):
        parts.append(row["description_ar"])

    combined_text = " | ".join(parts)
    return f"query: {combined_text}"

def main():
    print("Loading multilingual-e5-base model (this may take a minute if downloading)...")
    start_load = time.time()
    model = SentenceTransformer("intfloat/multilingual-e5-base")
    print(f"Model loaded in {time.time() - start_load:.1f}s")

    print(f"\nConnecting to database at {database_url()}...")
    with psycopg.connect(database_url()) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # Fetch all places
            print("Fetching places...")
            cur.execute("""
                SELECT id, name, name_ar, category, category_ar, description, description_ar
                FROM places
                ORDER BY id
            """)
            places = cur.fetchall()
            
            total_places = len(places)
            print(f"Found {total_places} places to process.")
            
            if total_places == 0:
                print("No places found. Exiting.")
                return

            batch_size = 64
            updates = []
            
            print(f"\nGenerating embeddings (batch size {batch_size})...")
            start_gen = time.time()
            
            for i in tqdm(range(0, total_places, batch_size)):
                batch = places[i:i + batch_size]
                
                # Build texts
                texts = [build_embedding_text(row) for row in batch]
                
                # Generate embeddings
                # We normalize embeddings since we use vector_cosine_ops which is equivalent to inner product for normalized vectors, and pgvector recommends it
                embeddings = model.encode(texts, normalize_embeddings=True)
                
                # Prepare updates (embedding, id)
                for row, emb in zip(batch, embeddings):
                    # psycopg vector support allows passing list/numpy array directly
                    updates.append((emb.tolist(), row["id"]))
            
            print(f"Generated embeddings in {time.time() - start_gen:.1f}s")
            
            # Write back to database
            print("\nUpdating database...")
            start_update = time.time()
            # Disable row_factory for the update query
            with conn.cursor() as update_cur:
                update_cur.executemany(
                    "UPDATE places SET embedding = %s, updated_at = now() WHERE id = %s",
                    updates
                )
            # Commit the transaction
            conn.commit()
            print(f"Database updated in {time.time() - start_update:.1f}s")
            
            # Verify update
            with conn.cursor() as check_cur:
                check_cur.execute("SELECT count(*) FROM places WHERE embedding IS NOT NULL")
                count = check_cur.fetchone()[0]
                print(f"\nVerification: {count}/{total_places} places have embeddings.")
            
if __name__ == "__main__":
    main()
