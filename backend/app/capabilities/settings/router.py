"""HTTP routes for the settings capability."""

from typing import Any

from fastapi import APIRouter

from . import service
from ..search.scheduler import reschedule
from ...models import Settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings() -> Settings:
    """Return the current application settings."""
    return service.get_settings()


@router.put("")
def put_settings(body: dict[str, Any]) -> Settings:
    """Save settings and update the periodic search schedule."""
    settings = service.save_settings(body)
    reschedule()
    return settings
