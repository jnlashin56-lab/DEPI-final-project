import os
import psycopg
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_URL")
base_dir = os.path.dirname(os.path.abspath(__file__))

print(f"Connecting to Supabase...")

try:
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            print("Applying schema...")
            with open(os.path.join(base_dir, "database", "schema.sql"), "r", encoding="utf-8") as f:
                cur.execute(f.read())
            
            print("Creating import tables...")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS import_places_english (
                name TEXT, latitude TEXT, longitude TEXT, category TEXT, description TEXT, place_id TEXT, price_egp TEXT
            );
            CREATE TABLE IF NOT EXISTS import_ticket_prices_english (
                site_name TEXT, governorate TEXT, heritage_type TEXT, egyptian_egp TEXT, egyptian_student_egp TEXT, foreign_egp TEXT, foreign_student_egp TEXT, visiting_hours TEXT
            );
            CREATE TABLE IF NOT EXISTS import_places_arabic (
                name_ar TEXT, latitude TEXT, longitude TEXT, category_ar TEXT, description_ar TEXT, place_id TEXT, price_egp TEXT
            );
            TRUNCATE import_places_english;
            TRUNCATE import_ticket_prices_english;
            TRUNCATE import_places_arabic;
            """)
            
            print("Copying CSV data...")
            with cur.copy("COPY import_places_english FROM STDIN WITH (FORMAT csv, HEADER true)") as copy:
                with open(os.path.join(base_dir, 'egypt_places_english.csv'), 'rb') as f:
                    copy.write(f.read())
            with cur.copy("COPY import_ticket_prices_english FROM STDIN WITH (FORMAT csv, HEADER true)") as copy:
                with open(os.path.join(base_dir, 'ticket_prices_english.csv'), 'rb') as f:
                    copy.write(f.read())
            with cur.copy("COPY import_places_arabic FROM STDIN WITH (FORMAT csv, HEADER true)") as copy:
                with open(os.path.join(base_dir, 'egypt_places_arabic.csv'), 'rb') as f:
                    copy.write(f.read())
            
            print("Inserting into actual tables...")
            cur.execute("""
            INSERT INTO places (source_place_id, name, name_ar, normalized_name, latitude, longitude, category, category_ar, description, description_ar, price_egp)
            SELECT
                NULLIF(en.place_id, '')::INTEGER, en.name, ar.name_ar, lower(trim(regexp_replace(en.name, '[^a-zA-Z0-9]+', ' ', 'g'))),
                NULLIF(en.latitude, '')::DOUBLE PRECISION, NULLIF(en.longitude, '')::DOUBLE PRECISION, NULLIF(en.category, ''), NULLIF(ar.category_ar, ''),
                NULLIF(en.description, ''), NULLIF(ar.description_ar, ''), NULLIF(en.price_egp, '')::NUMERIC(10, 2)
            FROM import_places_english en
            LEFT JOIN import_places_arabic ar ON NULLIF(en.place_id, '')::INTEGER = NULLIF(ar.place_id, '')::INTEGER
            WHERE NULLIF(en.name, '') IS NOT NULL
            ON CONFLICT (source_place_id) DO UPDATE SET
                name = EXCLUDED.name, name_ar = EXCLUDED.name_ar, normalized_name = EXCLUDED.normalized_name, latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude, category = EXCLUDED.category, category_ar = EXCLUDED.category_ar, description = EXCLUDED.description,
                description_ar = EXCLUDED.description_ar, price_egp = EXCLUDED.price_egp, updated_at = now();
            """)
            
            cur.execute("""
            INSERT INTO ticket_prices (site_name, normalized_site_name, governorate, heritage_type, egyptian_egp, egyptian_student_egp, foreign_egp, foreign_student_egp, visiting_hours)
            SELECT
                site_name, lower(trim(regexp_replace(site_name, '[^a-zA-Z0-9]+', ' ', 'g'))), NULLIF(governorate, ''), NULLIF(heritage_type, ''),
                NULLIF(egyptian_egp, '')::NUMERIC(10, 2), NULLIF(egyptian_student_egp, '')::NUMERIC(10, 2), NULLIF(foreign_egp, '')::NUMERIC(10, 2),
                NULLIF(foreign_student_egp, '')::NUMERIC(10, 2), NULLIF(visiting_hours, '')
            FROM import_ticket_prices_english
            WHERE NULLIF(site_name, '') IS NOT NULL
            ON CONFLICT (normalized_site_name) DO UPDATE SET
                site_name = EXCLUDED.site_name, governorate = EXCLUDED.governorate, heritage_type = EXCLUDED.heritage_type,
                egyptian_egp = EXCLUDED.egyptian_egp, egyptian_student_egp = EXCLUDED.egyptian_student_egp, foreign_egp = EXCLUDED.foreign_egp,
                foreign_student_egp = EXCLUDED.foreign_student_egp, visiting_hours = EXCLUDED.visiting_hours, updated_at = now();
            """)
            
            cur.execute("""
            INSERT INTO crowd_profiles (place_id, base_crowd_level, is_outdoor, notes)
            SELECT id, CASE WHEN lower(category) = 'historical' THEN 'high' WHEN lower(category) = 'cultural' THEN 'medium' ELSE 'low' END,
            CASE WHEN lower(category) IN ('museum', 'cultural') THEN false ELSE true END, 'Initial rule-based default profile for v1.'
            FROM places ON CONFLICT (place_id) DO NOTHING;
            """)
        conn.commit()
    print("Database fully migrated and seeded successfully!")
except Exception as e:
    print(f"Error: {e}")
