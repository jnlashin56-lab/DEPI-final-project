from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row
from mcp.server.fastmcp import FastMCP


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE_URL = (
    "postgresql://cultural_user:cultural_password@localhost:5432/cultural_recommender"
)

mcp = FastMCP("cultural-recommender")


def database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def read_csv_count(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        return sum(1 for _ in csv.DictReader(csv_file))


def query_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with psycopg.connect(database_url()) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)
            return list(cur.fetchall())


@mcp.tool()
def dataset_summary() -> dict[str, Any]:
    """Return row counts for the project CSV datasets."""

    files = {
        "english_places": PROJECT_ROOT / "egypt_places_english.csv",
        "arabic_places": PROJECT_ROOT / "egypt_places_arabic.csv",
        "english_ticket_prices": PROJECT_ROOT / "ticket_prices_english.csv",
        "arabic_ticket_prices": PROJECT_ROOT / "ticket_prices_arabic.csv",
    }

    return {
        name: {
            "path": str(path),
            "exists": path.exists(),
            "rows": read_csv_count(path) if path.exists() else None,
        }
        for name, path in files.items()
    }


@mcp.tool()
def database_status() -> dict[str, Any]:
    """Check the local Postgres database and return important table counts."""

    try:
        rows = query_all(
            """
            SELECT 'places' AS table_name, count(*)::int AS row_count FROM places
            UNION ALL
            SELECT 'ticket_prices', count(*)::int FROM ticket_prices
            UNION ALL
            SELECT 'crowd_profiles', count(*)::int FROM crowd_profiles
            UNION ALL
            SELECT 'places_with_arabic', count(*)::int
            FROM places
            WHERE name_ar IS NOT NULL AND category_ar IS NOT NULL
            """
        )
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
            "hint": "Start Docker with: docker compose up -d postgres",
        }

    return {
        "ok": True,
        "database_url": database_url(),
        "counts": {row["table_name"]: row["row_count"] for row in rows},
    }


@mcp.tool()
def search_places_by_name(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search bilingual places by English or Arabic name."""

    safe_limit = max(1, min(limit, 25))
    pattern = f"%{query}%"

    return query_all(
        """
        SELECT
            source_place_id,
            name,
            name_ar,
            category,
            category_ar,
            price_egp
        FROM places
        WHERE name ILIKE %s OR name_ar ILIKE %s
        ORDER BY name
        LIMIT %s
        """,
        (pattern, pattern, safe_limit),
    )


@mcp.tool()
def sample_places(category: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
    """Return sample places, optionally filtered by English category."""

    safe_limit = max(1, min(limit, 25))

    if category:
        return query_all(
            """
            SELECT
                source_place_id,
                name,
                name_ar,
                category,
                category_ar,
                left(description, 220) AS description_preview
            FROM places
            WHERE lower(category) = lower(%s)
            ORDER BY source_place_id
            LIMIT %s
            """,
            (category, safe_limit),
        )

    return query_all(
        """
        SELECT
            source_place_id,
            name,
            name_ar,
            category,
            category_ar,
            left(description, 220) AS description_preview
        FROM places
        ORDER BY source_place_id
        LIMIT %s
        """,
        (safe_limit,),
    )


if __name__ == "__main__":
    mcp.run()
