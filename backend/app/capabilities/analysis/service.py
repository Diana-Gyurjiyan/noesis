"""Prompt construction and normalization for paper relevance analysis."""

import json
import logging
import re
import time
from collections.abc import Mapping, Sequence
from typing import Any

from .llm import complete
from ...models import Analysis, Paper, Settings

logger = logging.getLogger("paper_radar.llm")

SYS = """You are a research assistant screening new papers against a researcher's thesis.
Judge ONLY from the material provided. Never invent results or future-work statements.
- paper.info = "abstract": you have title + abstract. If it does not mention future work, future_work = null.
- paper.info = "snippet": only a title and short search snippet; say so in the summary, keep relevance_score <= 6, future_work = null.
- paper.excerpt (when present) is text from the paper's own discussion/limitations/conclusion: base future_work on it
  (paraphrase; null if it names none).
Reply with ONE JSON object, no markdown, with keys:
summary (2-3 sentences), key_points (3-4 short strings),
relevance_score (0-10 integer), verdict ("relevant"|"partly"|"not_relevant"),
why_fits (2-3 short strings: concrete reasons it supports/connects to the thesis),
why_not (0-2 short strings: concrete reasons it does not fit or is a weak match),
future_work (string or null), cluster (2-4 word theme label; reuse labels from existing_clusters when they fit).
Write all text values in {lang_name}."""

def _lst(value: Any, maximum: int) -> list[str]:
    """Normalize a model value to a bounded list of strings.

    :param value: Arbitrary model output.
    :param maximum: Maximum number of items to retain.
    :returns: A list containing at most ``maximum`` strings.
    """
    if isinstance(value, str):
        value = [value]
    return [str(item) for item in (value or [])][:maximum]


def _norm(analysis: Mapping[str, Any], info: str) -> Analysis:
    """Validate and normalize model output, including score and enum bounds.

    :param analysis: Parsed JSON object returned by the model.
    :param info: Source material type, such as ``abstract`` or ``snippet``.
    :returns: A normalized analysis object safe for API use and persistence.
    """
    try:
        score = max(0, min(10, int(float(analysis.get("relevance_score", 0)))))
    except (TypeError, ValueError):
        score = 0
    future_work = analysis.get("future_work")
    if not future_work or str(future_work).strip().lower() in (
        "null", "none", "n/a", "no", "geen"
    ):
        future_work = None
    if info == "snippet":
        score, future_work = min(score, 6), None
    verdict = analysis.get("verdict")
    if verdict not in ("relevant", "partly", "not_relevant"):
        verdict = "relevant" if score >= 7 else "partly" if score >= 4 else "not_relevant"
    return {
        "summary": str(analysis.get("summary", "")),
        "key_points": _lst(analysis.get("key_points"), 4),
        "relevance_score": score,
        "verdict": verdict,
        "why_fits": _lst(analysis.get("why_fits"), 3),
        "why_not": _lst(analysis.get("why_not"), 2),
        "future_work": str(future_work) if future_work else None,
        "cluster": str(analysis.get("cluster") or "—")[:40],
        "info": info,
    }


def analyze(
    paper: Paper,
    settings: Settings,
    existing_clusters: Sequence[str],
    excerpt: str | None = None,
) -> Analysis:
    """Analyze a paper against the user's research focus.

    :param paper: Paper metadata and abstract.
    :param settings: Application settings, including language and LLM provider.
    :param existing_clusters: Existing labels to encourage consistent grouping.
    :param excerpt: Optional excerpt from the full text.
    :returns: Normalized relevance analysis.
    :raises ValueError: If the model returns invalid JSON after retrying.
    """
    lang = {"nl": "Dutch", "en": "English"}[settings["lang"]]
    info = "fulltext" if excerpt else paper.get("info", "abstract")
    pp = {**{k: paper[k] for k in ("title", "authors", "journal", "abstract")}, "info": "abstract" if excerpt else info}
    if excerpt: pp["excerpt"] = excerpt
    user = json.dumps({"thesis": settings["thesis"] or ", ".join(settings["topics"]), "keywords": settings["keywords"],
                       "existing_clusters": existing_clusters, "paper": pp}, ensure_ascii=False)
    system, last = SYS.format(lang_name=lang), None
    for attempt in range(2):
        started = time.monotonic()
        logger.info("LLM request started (provider=%s, model=%s, attempt=%d)", settings["llm"]["provider"],
                    settings["llm"]["model"], attempt + 1)
        try:
            raw = complete(system + ("\nReturn ONLY valid JSON." if attempt else ""), user, settings["llm"])
            result = _norm(json.loads(re.search(r"\{.*\}", raw, re.S).group(0)), info)
            logger.info("LLM request completed in %.1fs", time.monotonic() - started)
            return result
        except (json.JSONDecodeError, AttributeError) as e:
            last = e
    raise ValueError(f"Invalid LLM output after retrying: {last}")
