ALTER TABLE places
    ADD COLUMN IF NOT EXISTS name_ar TEXT,
    ADD COLUMN IF NOT EXISTS category_ar TEXT,
    ADD COLUMN IF NOT EXISTS description_ar TEXT;

CREATE TABLE IF NOT EXISTS import_places_arabic (
    name_ar TEXT,
    latitude TEXT,
    longitude TEXT,
    category_ar TEXT,
    description_ar TEXT,
    place_id TEXT,
    price_egp TEXT
);

TRUNCATE import_places_arabic;

COPY import_places_arabic
FROM '/workspace/egypt_places_arabic.csv'
WITH (FORMAT csv, HEADER true);

UPDATE places p
SET
    name_ar = NULLIF(ar.name_ar, ''),
    category_ar = NULLIF(ar.category_ar, ''),
    description_ar = NULLIF(ar.description_ar, ''),
    updated_at = now()
FROM import_places_arabic ar
WHERE p.source_place_id = NULLIF(ar.place_id, '')::INTEGER;
