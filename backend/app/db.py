import os
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from dotenv import load_dotenv

load_dotenv()

DEFAULT_DATABASE_URL = (
    "postgresql://cultural_user:cultural_password@localhost:5432/cultural_recommender"
)

def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

# Global connection pool
# We configure it with row_factory=dict_row so all connections return dicts by default.
pool = ConnectionPool(
    conninfo=get_database_url(),
    min_size=1,
    max_size=10,
    kwargs={"row_factory": dict_row},
    open=False, # We'll open it explicitly on startup
)

@contextmanager
def get_connection():
    """Context manager to get a connection from the pool."""
    with pool.connection() as conn:
        yield conn
