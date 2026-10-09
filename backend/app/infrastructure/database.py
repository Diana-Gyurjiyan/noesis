"""PostgreSQL connection and schema initialization."""

from typing import Any

import psycopg
from psycopg.rows import dict_row

from ..core.config import DATABASE_URL


def conn() -> psycopg.Connection[dict[str, Any]]:
    """Open a PostgreSQL connection that returns rows as dictionaries."""
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init() -> None:
    """Create database tables when they do not already exist."""
    with conn() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS settings (k TEXT PRIMARY KEY, v TEXT)"
        )
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS papers (
                id TEXT PRIMARY KEY, title TEXT, authors TEXT, abstract TEXT,
                url TEXT, source TEXT, journal TEXT, published TEXT,
                fetched_at TEXT, analysis TEXT, lang TEXT,
                favorite BOOLEAN NOT NULL DEFAULT FALSE
            )
            """
        )
        c.execute(
            """
            ALTER TABLE papers
            ADD COLUMN IF NOT EXISTS favorite BOOLEAN NOT NULL DEFAULT FALSE
            """
        )
