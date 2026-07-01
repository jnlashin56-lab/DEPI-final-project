from datetime import date, time
from typing import Optional

from backend.app.schemas import BookingRequest, BookingResponse, BookingAction


# ---------------------------------------------------------------------------
# Mock storage — replace with real Postgres queries once db.py exists.
# ---------------------------------------------------------------------------

_bookings_table: list[dict] = []
_next_booking_id = 1


def _reset_mock_db():
    """Test helper — clears mock storage between test runs."""
    global _bookings_table, _next_booking_id
    _bookings_table = []
    _next_booking_id = 1


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
# Saves a new booking with status "pending".
# ---------------------------------------------------------------------------

def create_booking(request: BookingRequest, price_egp: Optional[float] = None) -> BookingResponse:
    global _next_booking_id

    booking = {
        "booking_id": _next_booking_id,
        "status": "pending",
        "place_id": request.place_id,
        "visitor_name": request.visitor_name,
        "visitor_count": request.visitor_count,
        "visit_date": request.visit_date,
        "visit_time": request.visit_time,
        "total_price_egp": (price_egp * request.visitor_count) if price_egp else None,
    }
    _bookings_table.append(booking)
    _next_booking_id += 1

    return BookingResponse(
        **booking,
        message="Booking created, awaiting confirmation.",
    )


# ---------------------------------------------------------------------------
# confirm_booking — action="confirm_booking"
# Flips an existing booking's status to "confirmed".
# ---------------------------------------------------------------------------

def confirm_booking(booking_id: int) -> BookingResponse:
    for booking in _bookings_table:
        if booking["booking_id"] == booking_id:
            booking["status"] = "confirmed"
            return BookingResponse(
                **booking,
                message="Booking confirmed.",
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


# ---------------------------------------------------------------------------
# Quick manual test — run this file directly:
#   python -m backend.app.bookings
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # 1. Check availability
    print(check_availability(place_id=1, visit_date=date(2026, 7, 5), visit_time=time(10, 0)))

    # 2. Create a booking
    req = BookingRequest(
        place_id=1,
        visitor_name="Jana",
        visitor_count=2,
        visit_date=date(2026, 7, 5),
        visit_time=time(10, 0),
    )
    booking = create_booking(req, price_egp=200)
    print(booking)

    # 3. Confirm that booking
    confirmed = confirm_booking(booking.booking_id)
    print(confirmed)