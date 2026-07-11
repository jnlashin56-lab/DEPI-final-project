import os
import psycopg
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")

try:
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            # Drop the old constraint
            cur.execute("ALTER TABLE bookings DROP CONSTRAINT IF EXISTS booking_status_check;")
            # Add the new constraint allowing 'pending'
            cur.execute("ALTER TABLE bookings ADD CONSTRAINT booking_status_check CHECK (status IN ('pending', 'confirmed', 'cancelled'));")
        conn.commit()
    print("Database updated to allow 'pending' status!")
except Exception as e:
    print(f"Error: {e}")
