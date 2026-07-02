import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

def apply_migration(file_path: str):
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            with open(file_path, "r", encoding="utf-8") as f:
                sql = f.read()
            cur.execute(sql)
            conn.commit()
            print(f"Successfully applied {file_path}")

if __name__ == "__main__":
    apply_migration("database/migrations/create_bookings_table.sql")
