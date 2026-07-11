from datetime import date, time, datetime
from typing import Optional
import psycopg

from backend.app.schemas import BookingRequest, BookingResponse, BookingAction
from backend.app.db import pool

# ---------------------------------------------------------------------------
# Date / Time Parsers
# ---------------------------------------------------------------------------

def parse_date(date_str: str) -> Optional[date]:
    if not date_str: return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass
    return None

def parse_time(time_str: str) -> Optional[time]:
    if not time_str: return None
    time_str = time_str.strip().lower()
    for fmt in ("%H:%M", "%I %p", "%I%p", "%I:%M %p", "%I:%M%p"):
        try:
            return datetime.strptime(time_str, fmt).time()
        except ValueError:
            pass
    return None

# ---------------------------------------------------------------------------
# check_availability — action="check_availability"
# No real capacity data yet, so this always returns available=True.
# This is a deliberate placeholder: swap in a real slot-capacity check
# once ticket/capacity data is loaded.
# ---------------------------------------------------------------------------

def check_availability(place_id: int, visit_date: date, visit_time: time) -> dict:
    return {
        "place_id": place_id,
        "visit_date": visit_date,
        "visit_time": visit_time,
        "available": True,
        "message": "Slot available (no capacity limits enforced yet).",
    }


# ---------------------------------------------------------------------------
# create_booking — action="create_booking"
# Saves a new booking with status "pending" to the database.
# ---------------------------------------------------------------------------

def create_booking(request: BookingRequest, price_egp: Optional[float] = None) -> BookingResponse:
    total_price = (price_egp * request.visitor_count) if price_egp else None
    
    import uuid
    conf_code = str(uuid.uuid4())[:8].upper()

    with pool.connection() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                """
                INSERT INTO bookings (
                    place_id, visitor_name, visitor_count, visit_date, visit_time, status, total_price_egp, visitor_type, confirmation_code
                ) VALUES (%s, %s, %s, %s, %s, 'pending', %s, 'foreign', %s)
                RETURNING id;
                """,
                (request.place_id, request.visitor_name, request.visitor_count, request.visit_date, request.visit_time, total_price, conf_code)
            )
            booking_id = cur.fetchone()["id"]
            conn.commit()

    return BookingResponse(
        booking_id=booking_id,
        status="pending",
        place_id=request.place_id,
        visitor_name=request.visitor_name,
        visitor_count=request.visitor_count,
        visit_date=request.visit_date,
        visit_time=request.visit_time,
        total_price_egp=total_price,
        message="Booking created, awaiting confirmation.",
    )


# ---------------------------------------------------------------------------
# confirm_booking — action="confirm_booking"
# Flips an existing booking's status to "confirmed" in the database.
# ---------------------------------------------------------------------------

def confirm_booking(booking_id: int) -> BookingResponse:
    with pool.connection() as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                """
                UPDATE bookings 
                SET status = 'confirmed'
                WHERE id = %s
                RETURNING *;
                """,
                (booking_id,)
            )
            row = cur.fetchone()
            conn.commit()
            
    if row:
        return BookingResponse(
            booking_id=row["id"],
            status=row["status"],
            place_id=row["place_id"],
            visitor_name=row["visitor_name"],
            visitor_count=row["visitor_count"],
            visit_date=row["visit_date"],
            visit_time=row["visit_time"],
            total_price_egp=row["total_price_egp"] if row["total_price_egp"] is not None else None,
            message="Booking confirmed."
        )

    # No matching booking found
    return BookingResponse(
        booking_id=booking_id,
        status="failed",
        place_id=0,
        visitor_name="",
        visitor_count=0,
        visit_date=date.today(),
        visit_time=time(0, 0),
        message=f"No booking found with id {booking_id}.",
    )


# ---------------------------------------------------------------------------
# dispatch_action — the single entry point the Booking Agent calls.
# Reads action.action and routes to the matching function above.
# ---------------------------------------------------------------------------

def dispatch_action(action: BookingAction) -> dict:
    v_date = parse_date(action.visit_date) if action.visit_date else None
    v_time = parse_time(action.visit_time) if action.visit_time else None

    if action.action == "check_availability":
        if not v_date or not v_time:
            return {"status": "pending_info", "message": "Please provide a valid date (e.g. YYYY-MM-DD) and time (e.g. HH:MM)."}
        return check_availability(action.place_id, v_date, v_time)

    elif action.action == "create_booking":
        missing = []
        if not action.visitor_name: missing.append("name")
        if not action.visitor_count: missing.append("number of tickets")
        if not v_date: missing.append("date (e.g. YYYY-MM-DD)")
        if not v_time: missing.append("time (e.g. HH:MM)")
        
        if missing:
            return {"status": "pending_info", "message": f"Please provide your: {', '.join(missing)}."}
            
        request = BookingRequest(
            place_id=action.place_id,
            visitor_name=action.visitor_name,
            visitor_count=action.visitor_count,
            visit_date=v_date,
            visit_time=v_time,
        )
        return create_booking(request).model_dump()

    elif action.action == "confirm_booking":
        return confirm_booking(action.place_id).model_dump()

    else:
        return {"status": "failed", "message": f"Unknown action: {action.action}"}


if __name__ == "__main__":
    from backend.app.db import pool
    pool.open()
    try:
        # Test checking availability
        print(check_availability(place_id=793, visit_date=date(2026, 7, 5), visit_time=time(10, 0)))
    
        # Test creating a booking for Luxor Temple (id 793 in places)
        req = BookingRequest(
            place_id=793,
            visitor_name="Jana",
            visitor_count=2,
            visit_date=date(2026, 7, 5),
            visit_time=time(10, 0),
        )
        booking = create_booking(req, price_egp=200)
        print(booking)
    
        # Test confirming that booking
        confirmed = confirm_booking(booking.booking_id)
        print(confirmed)
    finally:
        pool.close()