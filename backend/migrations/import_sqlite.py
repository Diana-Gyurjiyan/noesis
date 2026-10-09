"""Copy existing SQLite settings and papers into the PostgreSQL database."""

import logging
import sqlite3
from pathlib import Path

from app.core.logging_config import configure_logging
from app.infrastructure import database

logger = logging.getLogger("paper_radar.migration")
SQLITE_PATH = Path(__file__).resolve().parents[1] / "radar.db"
PAPER_COLUMNS = (
    "id",
    "title",
    "authors",
    "abstract",
    "url",
    "source",
    "journal",
    "published",
    "fetched_at",
    "analysis",
    "lang",
)


def migrate(source_path: Path = SQLITE_PATH) -> tuple[int, int]:
    """Copy settings and paper records into PostgreSQL without overwriting data.

    Existing PostgreSQL rows take precedence when an identifier already exists.

    :param source_path: Path to the SQLite database to import.
    :returns: Number of imported settings and papers.
    """
    if not source_path.is_file():
        logger.info("No SQLite database found at %s; nothing to migrate", source_path)
        database.init()
        return 0, 0

    with sqlite3.connect(source_path) as source:
        source.row_factory = sqlite3.Row
        settings = source.execute("SELECT k, v FROM settings").fetchall()
        papers = source.execute(
            f"SELECT {', '.join(PAPER_COLUMNS)} FROM papers"
        ).fetchall()

    database.init()
    with database.conn() as destination:
        with destination.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO settings (k, v) VALUES (%s, %s)
                ON CONFLICT (k) DO NOTHING
                """,
                [(row["k"], row["v"]) for row in settings],
            )
            placeholders = ", ".join(["%s"] * len(PAPER_COLUMNS))
            columns = ", ".join(PAPER_COLUMNS)
            cursor.executemany(
                f"""
                INSERT INTO papers ({columns}) VALUES ({placeholders})
                ON CONFLICT (id) DO NOTHING
                """,
                [tuple(row[column] for column in PAPER_COLUMNS) for row in papers],
            )

    logger.info(
        "SQLite migration finished: %d settings and %d papers imported",
        len(settings),
        len(papers),
    )
    return len(settings), len(papers)


def main() -> None:
    """Run the one-time SQLite to PostgreSQL migration."""
    configure_logging()
    try:
        settings_count, papers_count = migrate()
    except Exception:
        logger.exception("SQLite migration failed")
        raise
    print(f"Imported {settings_count} settings and {papers_count} papers.")


if __name__ == "__main__":
    main()
