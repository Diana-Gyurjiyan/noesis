"""Search, analyze, and persist newly discovered research papers."""

import datetime as dt
import json
import logging
import time

from ..analysis import fulltext
from ..analysis.service import analyze
from ..discovery import sources
from ..papers import service as papers_service
from ..settings import service as settings_service
from ...models import Analysis, CurrentPaper, Paper, PipelineStatus

logger = logging.getLogger("paper_radar.pipeline")
STATE: PipelineStatus = {
    "running": False,
    "stage": "idle",
    "papers_found": 0,
    "papers_analyzed": 0,
    "analysis_limit": 5,
    "current_paper": None,
    "current_paper_data": None,
    "last_run": None,
    "last_new": 0,
    "error": None,
    "warnings": [],
}


def _norm(title: str) -> str:
    """Normalize a paper title for duplicate detection."""
    return "".join(char for char in title.lower() if char.isalnum())[:80]


def _current_paper(paper: Paper) -> CurrentPaper:
    """Build the safe, lightweight paper payload exposed during analysis."""
    return {
        "id": paper["id"],
        "title": paper["title"],
        "authors": paper.get("authors", ""),
        "journal": paper.get("journal", ""),
        "published": paper.get("published", ""),
        "url": paper.get("url", ""),
        "favorite": False,
        "analysis": {},
    }


def run_once() -> None:
    """Fetch, deduplicate, analyze, and persist papers for one scheduled run.

    Failed analyses are retried on subsequent runs. Both retries and new-paper
    analyses share the configured per-run analysis limit.
    """
    if STATE["running"]:
        logger.info("Search run skipped because another run is already active")
        return
    STATE.update(
        running=True,
        stage="loading_settings",
        papers_found=0,
        papers_analyzed=0,
        current_paper=None,
        current_paper_data=None,
        error=None,
        warnings=[],
    )
    started = time.monotonic()
    logger.info("Search run started; loading search and analysis settings")
    try:
        s = settings_service.get_settings()
        max_found = min(100, max(1, int(s.get("max_found_per_run", 20))))
        max_papers = min(50, max(1, int(s.get("max_papers_per_run", 5))))
        STATE["analysis_limit"] = max_papers
        logger.info(
            "Search configured for up to %d unique papers and %d LLM analyses using %s/%s",
            max_found,
            max_papers,
            s["llm"]["provider"],
            s["llm"]["model"],
        )
        STATE["stage"] = "searching_sources"
        found, warns = sources.fetch_all(s)
        STATE["warnings"] = warns
        STATE["papers_found"] = len(found)
        logger.info(
            "Source search complete: %d unique papers found; loading saved papers and retry queue",
            len(found),
        )
        new, analyzed = 0, 0
        STATE["stage"] = "loading_papers"
        rows = papers_service.list_paper_rows()
        known = {r["id"] for r in rows}
        titles = {_norm(r["title"]) for r in rows}
        clusters = list(
            {
                json.loads(r["analysis"]).get("cluster")
                for r in rows
                if r["analysis"] is not None
            }
            - {None}
        )
        retry_count = sum(
            bool(json.loads(row["analysis"] or "{}").get("error")) for row in rows
        )
        logger.info(
            "Database contains %d papers; %d failed analyses are eligible for retry",
            len(rows),
            retry_count,
        )
        for row in rows:
            previous = json.loads(row["analysis"] or "{}")
            if not previous.get("error"):
                continue
            if analyzed >= max_papers:
                break
            paper: Paper = {
                "id": row["id"],
                "title": row["title"],
                "authors": row["authors"],
                "journal": row["journal"],
                "abstract": row["abstract"],
                "url": row["url"],
                "source": row["source"],
                "published": row["published"],
            }
            paper["info"] = previous.get("info", "abstract")
            analyzed += 1
            STATE.update(
                stage="retrying_analysis",
                papers_analyzed=analyzed,
                current_paper=row["title"],
                current_paper_data=_current_paper(paper),
            )
            logger.info(
                "Retrying analysis %d/%d for previously failed paper: %s",
                analyzed,
                max_papers,
                row["title"],
            )
            try:
                analysis = analyze(paper, s, clusters)
            except Exception as e:
                warning = f"Retry analysis failed for '{row['title']}': {e}"
                STATE["warnings"].append(warning)
                logger.error(
                    "Retry analysis failed for paper %s: %s", row["id"], e
                )
                continue
            papers_service.save_analysis(row["id"], analysis, s["lang"])
            logger.info(
                "Retry analysis saved for '%s' (score=%d/10)",
                row["title"],
                analysis["relevance_score"],
            )
            if analysis.get("cluster") and analysis["cluster"] not in clusters:
                clusters.append(analysis["cluster"])
        skipped_due_to_limit = 0
        for paper in found:
            if (
                paper["id"] in known
                or _norm(paper["title"]) in titles
                or not paper["title"]
            ):
                continue
            if analyzed >= max_papers:
                skipped_due_to_limit += 1
                continue
            titles.add(_norm(paper["title"]))
            analyzed += 1
            STATE.update(
                stage="analyzing_papers",
                papers_analyzed=analyzed,
                current_paper=paper["title"],
                current_paper_data=_current_paper(paper),
            )
            logger.info(
                "Analyzing paper %d/%d with %s/%s: %s",
                analyzed,
                max_papers,
                s["llm"]["provider"],
                s["llm"]["model"],
                paper["title"],
            )
            try:
                analysis = analyze(paper, s, clusters)
            except Exception as e:
                analysis = Analysis(
                    error=str(e), info=paper.get("info", "abstract")
                )
                warning = f"Analysis failed for '{paper['title']}': {e}"
                STATE["warnings"].append(warning)
                logger.error("Analysis failed for paper %s: %s", paper["id"], e)
            if (
                s["fulltext"]
                and not analysis.get("error")
                and analysis["relevance_score"] >= s["fulltext_min_score"]
            ):
                excerpt = fulltext.excerpt(paper)
                if excerpt:
                    STATE["stage"] = "analyzing_full_text"
                    logger.info("Running full-text analysis for '%s'", paper["title"])
                    try:
                        analysis = analyze(paper, s, clusters, excerpt=excerpt)
                    except Exception as e:
                        STATE["warnings"].append(
                            f"Full-text analysis failed for '{paper['title']}': {e}"
                        )
                        logger.error(
                            "Full-text analysis failed for paper %s: %s",
                            paper["id"],
                            e,
                        )
            if analysis.get("cluster") and analysis["cluster"] not in clusters:
                clusters.append(analysis["cluster"])
            papers_service.save_new_paper(paper, analysis, s["lang"])
            new += 1
            STATE["stage"] = "saving_papers"
            logger.info(
                "Paper saved and available to the frontend: '%s' (score=%s/10)",
                paper["title"],
                analysis.get("relevance_score", "unavailable"),
            )
        if skipped_due_to_limit:
            logger.info(
                "%d additional found papers were not analyzed because the per-run LLM limit (%d) was reached",
                skipped_due_to_limit,
                max_papers,
            )
        STATE.update(last_run=dt.datetime.now().isoformat(), last_new=new)
        STATE["stage"] = "complete"
        STATE["current_paper"] = None
        STATE["current_paper_data"] = None
        logger.info(
            "Search run completed: %d new papers, %d analyses (limit=%d), %d warnings in %.1fs",
            new, analyzed, max_papers, len(STATE["warnings"]), time.monotonic() - started,
        )
    except Exception as e:
        STATE["error"] = str(e)
        logger.exception("Search run failed")
    finally:
        STATE["running"] = False
        if STATE["error"]:
            STATE["stage"] = "failed"
        elif STATE["stage"] != "complete":
            STATE["stage"] = "idle"
        STATE["current_paper"] = None
        STATE["current_paper_data"] = None
