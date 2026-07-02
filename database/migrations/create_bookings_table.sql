CREATE TABLE IF NOT EXISTS bookings (
    booking_id BIGSERIAL PRIMARY KEY,
    place_id BIGINT NOT NULL REFERENCES places(id),
    visitor_name TEXT NOT NULL,
    visitor_count INTEGER NOT NULL,
    visit_date DATE NOT NULL,
    visit_time TIME NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    total_price_egp NUMERIC(10, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
