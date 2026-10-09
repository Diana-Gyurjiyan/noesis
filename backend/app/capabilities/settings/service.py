"""Use cases for managing application settings."""

from collections.abc import Mapping
from typing import Any

from . import repository
from ...models import Settings


def get_settings() -> Settings:
    """Return the effective settings, including defaults."""
    return repository.get_settings()


def save_settings(settings: Mapping[str, Any]) -> Settings:
    """Save settings and return their effective persisted form."""
    repository.save_settings(settings)
    return repository.get_settings()
