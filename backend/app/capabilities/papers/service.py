"""Use cases for browsing and managing the paper library."""

from . import repository
from ...models import Analysis, Paper


def list_papers(min_score: int = 0) -> list[Paper]:
    """Return saved papers meeting the minimum relevance score."""
    return repository.list_papers(min_score)


def set_favorite(paper_id: str, favorite: bool) -> bool:
    """Persist a paper's favorite state."""
    return repository.update_favorite(paper_id, favorite)


def remove_paper(paper_id: str) -> bool:
    """Remove a paper and its analysis."""
    return repository.delete_paper(paper_id)


def save_analysis(paper_id: str, analysis: Analysis, language: str) -> None:
    """Save analysis results to an existing paper."""
    repository.update_analysis(paper_id, analysis, language)


def list_paper_rows() -> list[dict[str, object]]:
    """Return paper rows for search-run deduplication and retry handling."""
    return repository.list_paper_rows()


def save_new_paper(paper: Paper, analysis: Analysis, language: str) -> None:
    """Save a new paper and its analysis."""
    repository.insert_analyzed_paper(paper, analysis, language)
