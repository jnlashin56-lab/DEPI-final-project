from datetime import date, time
from typing import Optional
import psycopg

from backend.app.schemas import BookingRequest, BookingResponse, BookingAction
from backend.app.db import pool

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
    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO bookings (
                    place_id, visitor_name, visitor_count, visit_date, visit_time, status, total_price_egp
                ) VALUES (%s, %s, %s, %s, %s, 'pending', %s)
                RETURNING booking_id;
                """,
                (request.place_id, request.visitor_name, request.visitor_count, request.visit_date, request.visit_time, total_price)
            )
            booking_id = cur.fetchone()["booking_id"]
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
                WHERE booking_id = %s
                RETURNING *;
                """,
                (booking_id,)
            )
            row = cur.fetchone()
            conn.commit()
            
    if row:
        return BookingResponse(
            booking_id=row["booking_id"],
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
    if action.action == "check_availability":
        return check_availability(action.place_id, action.visit_date, action.visit_time)

    elif action.action == "create_booking":
        missing = []
        if not action.visitor_name: missing.append("name")
        if not action.visitor_count: missing.append("number of tickets")
        if not action.visit_date: missing.append("date")
        if not action.visit_time: missing.append("time")
        
        if missing:
            return {"status": "pending_info", "message": f"Please provide your: {', '.join(missing)}."}
            
        request = BookingRequest(
            place_id=action.place_id,
            visitor_name=action.visitor_name,
            visitor_count=action.visitor_count,
            visit_date=action.visit_date,
            visit_time=action.visit_time,
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