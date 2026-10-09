"""HTTP routes for the paper library capability."""

import logging

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from . import service
from ...models import Paper

router = APIRouter(prefix="/api/papers", tags=["papers"])


class FavoriteUpdate(BaseModel):
    """Request body for setting a paper's favorite state."""

    favorite: bool


@router.get("")
def list_papers(min_score: int = 0) -> list[Paper]:
    """Return stored papers meeting the requested minimum score."""
    return service.list_papers(min_score)


@router.put("/{paper_id}/favorite")
def set_favorite(paper_id: str, body: FavoriteUpdate) -> dict[str, bool]:
    """Set and persist a paper's favorite state."""
    if not service.set_favorite(paper_id, body.favorite):
        raise HTTPException(status_code=404, detail="Paper not found")
    logging.getLogger("paper_radar.api").info(
        "Paper favorite updated (paper_id=%s, favorite=%s)",
        paper_id,
        body.favorite,
    )
    return {"favorite": body.favorite}


@router.delete("/{paper_id}", status_code=204)
def delete_paper(paper_id: str) -> Response:
    """Permanently delete a paper and its analysis."""
    if not service.remove_paper(paper_id):
        raise HTTPException(status_code=404, detail="Paper not found")
    logging.getLogger("paper_radar.api").info("Paper deleted (paper_id=%s)", paper_id)
    return Response(status_code=204)
