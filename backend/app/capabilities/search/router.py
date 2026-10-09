"""HTTP routes for starting and monitoring search runs."""

from fastapi import APIRouter, BackgroundTasks

from . import service
from ...models import PipelineStatus

router = APIRouter(prefix="/api", tags=["search"])


@router.post("/run")
def start_run(background_tasks: BackgroundTasks) -> dict[str, bool]:
    """Queue a single search run."""
    background_tasks.add_task(service.run_once)
    return {"started": True}


@router.get("/status")
def get_status() -> PipelineStatus:
    """Return the current search-run status."""
    return service.STATE
