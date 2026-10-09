"""PostgreSQL repository for user settings."""

import json
from collections.abc import Mapping
from typing import Any, cast

from ...infrastructure.database import conn
from ...models import Settings

DEFAULTS: Settings = {
    "thesis": "",
    "topics": [],
    "keywords": [],
    "journals": [],
    "frequency_days": 3,
    "lang": "nl",
    "sources": ["arxiv", "openalex", "semanticscholar", "pubmed"],
    "max_per_run": 25,
    "max_found_per_run": 20,
    "max_papers_per_run": 5,
    "fulltext": True,
    "fulltext_min_score": 5,
    "llm": {"provider": "ollama", "model": "qwen3:8b"},
}

LEGACY_LLM_DEFAULT = {"provider": "anthropic", "model": "claude-sonnet-4-6"}


def get_settings() -> Settings:
    """Load current settings and fill missing values from the defaults."""
    with conn() as connection:
        rows = {
            row["k"]: json.loads(row["v"])
            for row in connection.execute("SELECT * FROM settings")
        }
        if rows.get("llm") == LEGACY_LLM_DEFAULT:
            rows["llm"] = DEFAULTS["llm"].copy()
            connection.execute(
                """
                INSERT INTO settings (k, v) VALUES (%s, %s)
                ON CONFLICT (k) DO UPDATE SET v = EXCLUDED.v
                """,
                ("llm", json.dumps(rows["llm"])),
            )
    return cast(Settings, {**DEFAULTS, **rows})


def save_settings(settings: Mapping[str, Any]) -> None:
    """Persist supplied settings fields."""
    with conn() as connection:
        for key, value in settings.items():
            connection.execute(
                """
                INSERT INTO settings (k, v) VALUES (%s, %s)
                ON CONFLICT (k) DO UPDATE SET v = EXCLUDED.v
                """,
                (key, json.dumps(value)),
            )
