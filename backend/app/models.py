"""Shared type definitions for papers, analyses, and application settings.

These TypedDicts describe the JSON-shaped data exchanged between the
application layers.
"""

from typing import Literal, NotRequired, TypedDict


class LLMConfig(TypedDict):
    """Configuration for a language model provider."""

    provider: Literal["ollama", "anthropic", "openai"]
    model: str


class Settings(TypedDict):
    """Complete application settings returned by the database layer."""

    thesis: str
    topics: list[str]
    keywords: list[str]
    journals: list[str]
    frequency_days: int
    lang: Literal["nl", "en"]
    sources: list[str]
    max_per_run: int
    max_found_per_run: int
    max_papers_per_run: int
    fulltext: bool
    fulltext_min_score: int
    llm: LLMConfig


class Paper(TypedDict):
    """Paper metadata returned by a configured search source."""

    id: str
    title: str
    authors: str
    abstract: str
    url: str
    source: str
    journal: str
    published: str
    fetched_at: NotRequired[str]
    analysis: NotRequired["Analysis"]
    lang: NotRequired[str]
    favorite: NotRequired[bool]
    info: NotRequired[str]
    pdf: NotRequired[str]
    doi: NotRequired[str]


class Analysis(TypedDict, total=False):
    """Normalized paper-analysis result or analysis error."""

    summary: str
    key_points: list[str]
    relevance_score: int
    verdict: Literal["relevant", "partly", "not_relevant"]
    why_fits: list[str]
    why_not: list[str]
    future_work: str | None
    cluster: str
    info: str
    error: str


class CurrentPaper(TypedDict):
    """Paper metadata shown while its analysis is still running."""

    id: str
    title: str
    authors: str
    journal: str
    published: str
    url: str
    favorite: bool
    analysis: Analysis


class PipelineStatus(TypedDict):
    """Current state exposed by the pipeline status endpoint."""

    running: bool
    stage: str
    papers_found: int
    papers_analyzed: int
    analysis_limit: int
    current_paper: str | None
    current_paper_data: NotRequired[CurrentPaper | None]
    last_run: str | None
    last_new: int
    error: str | None
    warnings: list[str]
