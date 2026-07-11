"""
Admin API router — all CRUD endpoints for the admin panel.

All routes are protected by JWT authentication via get_current_admin dependency.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.auth import verify_credentials, create_token, get_current_admin
from backend.app.db import get_connection
from backend.app.schemas import (
    AdminLogin, TokenResponse,
    PlaceCreate, PlaceUpdate, PlaceAdmin, PlaceListResponse,
    TicketPriceAdmin, TicketPriceUpdate,
    BookingAdmin,
    CrowdProfileAdmin, CrowdProfileUpdate,
    AnalyticsResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
def admin_login(body: AdminLogin):
    if not verify_credentials(body.username, body.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(body.username)
    return TokenResponse(access_token=token)


# ---------------------------------------------------------------------------
# Places CRUD
# ---------------------------------------------------------------------------

@router.get("/places", response_model=PlaceListResponse)
def list_places(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    category: Optional[str] = None,
    _admin: str = Depends(get_current_admin),
):
    offset = (page - 1) * page_size
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Build WHERE clause
            conditions = []
            params = []
            if search:
                conditions.append("(LOWER(name) LIKE LOWER(%s) OR LOWER(name_ar) LIKE LOWER(%s))")
                params.extend([f"%{search}%", f"%{search}%"])
            if category:
                conditions.append("LOWER(category) = LOWER(%s)")
                params.append(category)

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            # Count
            cur.execute(f"SELECT COUNT(*) FROM places {where}", params)
            total = cur.fetchone()["count"]

            # Fetch page
            cur.execute(
                f"""SELECT id, source_place_id, name, name_ar, category, category_ar,
                       description, description_ar, price_egp, latitude, longitude,
                       (embedding IS NOT NULL) AS has_embedding,
                       created_at::text, updated_at::text
                FROM places {where}
                ORDER BY id
                LIMIT %s OFFSET %s""",
                params + [page_size, offset],
            )
            rows = cur.fetchall()

    places = [PlaceAdmin(**row) for row in rows]
    return PlaceListResponse(places=places, total=total, page=page, page_size=page_size)


@router.get("/places/{place_id}", response_model=PlaceAdmin)
def get_place(place_id: int, _admin: str = Depends(get_current_admin)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, source_place_id, name, name_ar, category, category_ar,
                       description, description_ar, price_egp, latitude, longitude,
                       (embedding IS NOT NULL) AS has_embedding,
                       created_at::text, updated_at::text
                FROM places WHERE id = %s""",
                (place_id,),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Place not found")
    return PlaceAdmin(**row)


def _normalize(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def _reembed_place(place_id: int, conn):
    """Re-generate embedding for a single place after description change."""
    from backend.app.retrieval import get_model

    with conn.cursor() as cur:
        cur.execute(
            "SELECT name, name_ar, category, category_ar, description, description_ar FROM places WHERE id = %s",
            (place_id,),
        )
        row = cur.fetchone()
        if not row:
            return

    # Build embedding text (same logic as generate_embeddings.py)
    parts = []
    for field in ["name", "category", "description", "name_ar", "category_ar", "description_ar"]:
        if row.get(field):
            parts.append(row[field])
    text = f"query: {' | '.join(parts)}"

    model = get_model()
    embedding = model.encode([text], normalize_embeddings=True)[0].tolist()

    with conn.cursor() as cur:
        cur.execute(
            "UPDATE places SET embedding = %s, updated_at = now() WHERE id = %s",
            (embedding, place_id),
        )
    conn.commit()
    logger.info(f"Re-embedded place {place_id}")


@router.post("/places", response_model=PlaceAdmin)
def create_place(body: PlaceCreate, _admin: str = Depends(get_current_admin)):
    normalized = _normalize(body.name)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO places (name, name_ar, normalized_name, category, category_ar,
                       description, description_ar, price_egp, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id""",
                (body.name, body.name_ar, normalized, body.category, body.category_ar,
                 body.description, body.description_ar, body.price_egp,
                 body.latitude, body.longitude),
            )
            new_id = cur.fetchone()["id"]
            conn.commit()

        # Generate embedding for the new place
        if body.description or body.name:
            try:
                _reembed_place(new_id, conn)
            except Exception as e:
                logger.error(f"Failed to embed new place {new_id}: {e}")

    return get_place(new_id, _admin)


@router.put("/places/{place_id}", response_model=PlaceAdmin)
def update_place(place_id: int, body: PlaceUpdate, _admin: str = Depends(get_current_admin)):
    with get_connection() as conn:
        # Fetch current values to check if description changed
        with conn.cursor() as cur:
            cur.execute("SELECT description, description_ar FROM places WHERE id = %s", (place_id,))
            old = cur.fetchone()
        if not old:
            raise HTTPException(status_code=404, detail="Place not found")

        description_changed = (
            (body.description or "") != (old.get("description") or "")
            or (body.description_ar or "") != (old.get("description_ar") or "")
        )

        normalized = _normalize(body.name)
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE places SET
                    name = %s, name_ar = %s, normalized_name = %s,
                    category = %s, category_ar = %s,
                    description = %s, description_ar = %s,
                    price_egp = %s, latitude = %s, longitude = %s,
                    updated_at = now()
                WHERE id = %s""",
                (body.name, body.name_ar, normalized, body.category, body.category_ar,
                 body.description, body.description_ar, body.price_egp,
                 body.latitude, body.longitude, place_id),
            )
            conn.commit()

        # Only re-embed if description actually changed
        if description_changed:
            try:
                _reembed_place(place_id, conn)
            except Exception as e:
                logger.error(f"Failed to re-embed place {place_id}: {e}")

    return get_place(place_id, _admin)


@router.delete("/places/{place_id}")
def delete_place(place_id: int, _admin: str = Depends(get_current_admin)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM places WHERE id = %s RETURNING id", (place_id,))
            deleted = cur.fetchone()
            conn.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="Place not found")
    return {"message": f"Place {place_id} deleted"}


# ---------------------------------------------------------------------------
# Ticket Prices
# ---------------------------------------------------------------------------

@router.get("/ticket-prices", response_model=list[TicketPriceAdmin])
def list_ticket_prices(
    search: Optional[str] = None,
    _admin: str = Depends(get_current_admin),
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            if search:
                cur.execute(
                    """SELECT id, site_name, governorate, heritage_type,
                           egyptian_egp, egyptian_student_egp, foreign_egp, foreign_student_egp,
                           visiting_hours
                    FROM ticket_prices
                    WHERE LOWER(site_name) LIKE LOWER(%s) OR LOWER(governorate) LIKE LOWER(%s)
                    ORDER BY site_name""",
                    (f"%{search}%", f"%{search}%"),
                )
            else:
                cur.execute(
                    """SELECT id, site_name, governorate, heritage_type,
                           egyptian_egp, egyptian_student_egp, foreign_egp, foreign_student_egp,
                           visiting_hours
                    FROM ticket_prices ORDER BY site_name"""
                )
            rows = cur.fetchall()
    return [TicketPriceAdmin(**row) for row in rows]


@router.put("/ticket-prices/{price_id}", response_model=TicketPriceAdmin)
def update_ticket_price(price_id: int, body: TicketPriceUpdate, _admin: str = Depends(get_current_admin)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE ticket_prices SET
                    egyptian_egp = COALESCE(%s, egyptian_egp),
                    egyptian_student_egp = COALESCE(%s, egyptian_student_egp),
                    foreign_egp = COALESCE(%s, foreign_egp),
                    foreign_student_egp = COALESCE(%s, foreign_student_egp),
                    visiting_hours = COALESCE(%s, visiting_hours),
                    updated_at = now()
                WHERE id = %s
                RETURNING id, site_name, governorate, heritage_type,
                    egyptian_egp, egyptian_student_egp, foreign_egp, foreign_student_egp,
                    visiting_hours""",
                (body.egyptian_egp, body.egyptian_student_egp, body.foreign_egp,
                 body.foreign_student_egp, body.visiting_hours, price_id),
            )
            row = cur.fetchone()
            conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Ticket price not found")
    return TicketPriceAdmin(**row)


# ---------------------------------------------------------------------------
# Bookings Dashboard
# ---------------------------------------------------------------------------

@router.get("/bookings", response_model=list[BookingAdmin])
def list_bookings(
    status: Optional[str] = None,
    place_id: Optional[int] = None,
    _admin: str = Depends(get_current_admin),
):
    with get_connection() as conn:
        with conn.cursor() as cur:
            conditions = []
            params = []
            if status:
                conditions.append("b.status = %s")
                params.append(status)
            if place_id:
                conditions.append("b.place_id = %s")
                params.append(place_id)

            where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

            cur.execute(
                f"""SELECT b.id, b.place_id, p.name AS place_name,
                       b.visitor_name, b.visitor_type, b.visitor_count,
                       b.visit_date, b.visit_time, b.status,
                       b.total_price_egp, b.confirmation_code,
                       b.created_at::text
                FROM bookings b
                LEFT JOIN places p ON p.id = b.place_id
                {where}
                ORDER BY b.created_at DESC""",
                params,
            )
            rows = cur.fetchall()
    return [BookingAdmin(**row) for row in rows]


@router.patch("/bookings/{booking_id}/confirm")
def confirm_booking(booking_id: int, _admin: str = Depends(get_current_admin)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE bookings SET status = 'confirmed' WHERE id = %s RETURNING id, status",
                (booking_id,),
            )
            row = cur.fetchone()
            conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"message": f"Booking {booking_id} confirmed", "status": "confirmed"}


@router.patch("/bookings/{booking_id}/cancel")
def cancel_booking(booking_id: int, _admin: str = Depends(get_current_admin)):
    """Soft cancel — sets status to 'cancelled', never deletes the row."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE bookings SET status = 'cancelled' WHERE id = %s RETURNING id, status",
                (booking_id,),
            )
            row = cur.fetchone()
            conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"message": f"Booking {booking_id} cancelled", "status": "cancelled"}


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(_admin: str = Depends(get_current_admin)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Total bookings
            cur.execute("SELECT COUNT(*) FROM bookings")
            total_bookings = cur.fetchone()["count"]

            # Total revenue
            cur.execute("SELECT COALESCE(SUM(total_price_egp), 0) FROM bookings WHERE status != 'cancelled'")
            total_revenue = float(cur.fetchone()["coalesce"])

            # Active places
            cur.execute("SELECT COUNT(*) FROM places")
            active_places = cur.fetchone()["count"]

            # Places with embeddings
            cur.execute("SELECT COUNT(*) FROM places WHERE embedding IS NOT NULL")
            places_with_embeddings = cur.fetchone()["count"]

            # Top 10 most-booked places
            cur.execute(
                """SELECT p.name, COUNT(b.id) AS booking_count
                FROM bookings b JOIN places p ON p.id = b.place_id
                WHERE b.status != 'cancelled'
                GROUP BY p.name
                ORDER BY booking_count DESC LIMIT 10"""
            )
            top_booked = [{"name": r["name"], "count": r["booking_count"]} for r in cur.fetchall()]

            # Bookings by status
            cur.execute("SELECT status, COUNT(*) FROM bookings GROUP BY status")
            by_status = {r["status"]: r["count"] for r in cur.fetchall()}

            # Recent 10 bookings
            cur.execute(
                """SELECT b.id, p.name AS place_name, b.visitor_name, b.status,
                       b.created_at::text
                FROM bookings b LEFT JOIN places p ON p.id = b.place_id
                ORDER BY b.created_at DESC LIMIT 10"""
            )
            recent = [dict(r) for r in cur.fetchall()]

    return AnalyticsResponse(
        total_bookings=total_bookings,
        total_revenue=total_revenue,
        active_places=active_places,
        places_with_embeddings=places_with_embeddings,
        top_booked_places=top_booked,
        bookings_by_status=by_status,
        recent_bookings=recent,
    )


# ---------------------------------------------------------------------------
# Crowd Profiles (nice-to-have)
# ---------------------------------------------------------------------------

@router.get("/crowd-profiles", response_model=list[CrowdProfileAdmin])
def list_crowd_profiles(_admin: str = Depends(get_current_admin)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT cp.place_id, p.name AS place_name,
                       cp.base_crowd_level, cp.peak_hours, cp.peak_season_months,
                       cp.is_outdoor, cp.notes
                FROM crowd_profiles cp
                JOIN places p ON p.id = cp.place_id
                ORDER BY p.name"""
            )
            rows = cur.fetchall()
    return [CrowdProfileAdmin(**row) for row in rows]


@router.put("/crowd-profiles/{place_id}", response_model=CrowdProfileAdmin)
def update_crowd_profile(place_id: int, body: CrowdProfileUpdate, _admin: str = Depends(get_current_admin)):
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Upsert
            cur.execute(
                """INSERT INTO crowd_profiles (place_id, base_crowd_level, peak_hours, peak_season_months, is_outdoor, notes)
                VALUES (%s, %s, %s, %s, COALESCE(%s, true), %s)
                ON CONFLICT (place_id) DO UPDATE SET
                    base_crowd_level = EXCLUDED.base_crowd_level,
                    peak_hours = EXCLUDED.peak_hours,
                    peak_season_months = EXCLUDED.peak_season_months,
                    is_outdoor = COALESCE(EXCLUDED.is_outdoor, crowd_profiles.is_outdoor),
                    notes = EXCLUDED.notes,
                    updated_at = now()
                RETURNING place_id""",
                (place_id, body.base_crowd_level, body.peak_hours,
                 body.peak_season_months, body.is_outdoor, body.notes),
            )
            conn.commit()

        # Re-fetch with place name
        with conn.cursor() as cur:
            cur.execute(
                """SELECT cp.place_id, p.name AS place_name,
                       cp.base_crowd_level, cp.peak_hours, cp.peak_season_months,
                       cp.is_outdoor, cp.notes
                FROM crowd_profiles cp
                JOIN places p ON p.id = cp.place_id
                WHERE cp.place_id = %s""",
                (place_id,),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Crowd profile not found")
    return CrowdProfileAdmin(**row)
