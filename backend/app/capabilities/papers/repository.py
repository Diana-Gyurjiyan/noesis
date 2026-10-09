"""PostgreSQL repository for discovered and analyzed papers."""

import datetime as dt
import json
from typing import Any

from ...infrastructure.database import conn
from ...models import Analysis, Paper


def list_raw_papers() -> list[dict[str, Any]]:
    """Return stored paper rows in publication order."""
    with conn() as connection:
        return [
            dict(row)
            for row in connection.execute("SELECT * FROM papers ORDER BY published DESC")
        ]


def list_paper_rows() -> list[dict[str, Any]]:
    """Return all stored rows for search-pipeline deduplication and retries."""
    with conn() as connection:
        return [dict(row) for row in connection.execute("SELECT * FROM papers")]


def list_papers(min_score: int = 0) -> list[Paper]:
    """Return papers whose analysis meets the requested minimum score."""
    result: list[Paper] = []
    for row in list_raw_papers():
        analysis = json.loads(row["analysis"] or "{}")
        if analysis.get("relevance_score", 0) < min_score:
            continue
        result.append({**row, "analysis": analysis})
    return result


def update_favorite(paper_id: str, favorite: bool) -> bool:
    """Set a paper's favorite flag; return whether the paper exists."""
    with conn() as connection:
        row = connection.execute(
            "UPDATE papers SET favorite=%s WHERE id=%s RETURNING id",
            (favorite, paper_id),
        ).fetchone()
    return row is not None


def delete_paper(paper_id: str) -> bool:
    """Delete a paper; return whether it existed."""
    with conn() as connection:
        row = connection.execute(
            "DELETE FROM papers WHERE id=%s RETURNING id",
            (paper_id,),
        ).fetchone()
    return row is not None


def update_analysis(paper_id: str, analysis: Analysis, language: str) -> None:
    """Persist a fresh analysis for an existing paper."""
    with conn() as connection:
        connection.execute(
            "UPDATE papers SET analysis=%s, lang=%s WHERE id=%s",
            (json.dumps(analysis, ensure_ascii=False), language, paper_id),
        )


def insert_analyzed_paper(paper: Paper, analysis: Analysis, language: str) -> None:
    """Insert a newly analyzed paper without replacing an existing record."""
    with conn() as connection:
        connection.execute(
            """
            INSERT INTO papers
                (id, title, authors, abstract, url, source, journal, published,
                 fetched_at, analysis, lang)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            """,
            (
                paper["id"],
                paper["title"],
                paper["authors"],
                paper["abstract"],
                paper["url"],
                paper["source"],
                paper["journal"],
                paper["published"],
                dt.datetime.now().isoformat(),
                json.dumps(analysis, ensure_ascii=False),
                language,
            ),
        )
