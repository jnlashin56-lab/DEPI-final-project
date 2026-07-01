CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS places (
    id BIGSERIAL PRIMARY KEY,
    source_place_id INTEGER UNIQUE,
    name TEXT NOT NULL,
    name_ar TEXT,
    normalized_name TEXT NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    category TEXT,
    category_ar TEXT,
    description TEXT,
    description_ar TEXT,
    price_egp NUMERIC(10, 2),
    embedding VECTOR(768),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_places_normalized_name
    ON places (normalized_name);

CREATE INDEX IF NOT EXISTS idx_places_category
    ON places (category);

CREATE INDEX IF NOT EXISTS idx_places_embedding
    ON places
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE TABLE IF NOT EXISTS ticket_prices (
    id BIGSERIAL PRIMARY KEY,
    site_name TEXT NOT NULL,
    normalized_site_name TEXT NOT NULL UNIQUE,
    governorate TEXT,
    heritage_type TEXT,
    egyptian_egp NUMERIC(10, 2),
    egyptian_student_egp NUMERIC(10, 2),
    foreign_egp NUMERIC(10, 2),
    foreign_student_egp NUMERIC(10, 2),
    visiting_hours TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ticket_prices_normalized_site_name
    ON ticket_prices (normalized_site_name);

CREATE TABLE IF NOT EXISTS crowd_profiles (
    place_id BIGINT PRIMARY KEY REFERENCES places(id) ON DELETE CASCADE,
    base_crowd_level TEXT NOT NULL DEFAULT 'medium',
    peak_hours TEXT[] NOT NULL DEFAULT ARRAY['10:00-14:00'],
    peak_season_months INTEGER[] NOT NULL DEFAULT ARRAY[10, 11, 12, 1, 2, 3, 4],
    is_outdoor BOOLEAN NOT NULL DEFAULT true,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT crowd_level_check CHECK (base_crowd_level IN ('low', 'medium', 'high'))
);

CREATE TABLE IF NOT EXISTS bookings (
    id BIGSERIAL PRIMARY KEY,
    place_id BIGINT NOT NULL REFERENCES places(id),
    visitor_name TEXT NOT NULL,
    visitor_type TEXT NOT NULL,
    visitor_count INTEGER NOT NULL CHECK (visitor_count > 0),
    visit_date DATE NOT NULL,
    visit_time TIME,
    status TEXT NOT NULL DEFAULT 'confirmed',
    total_price_egp NUMERIC(10, 2),
    confirmation_code TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT visitor_type_check CHECK (
        visitor_type IN (
            'egyptian',
            'egyptian_student',
            'foreign',
            'foreign_student'
        )
    ),
    CONSTRAINT booking_status_check CHECK (status IN ('confirmed', 'cancelled'))
);
