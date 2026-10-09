"""Search providers used to retrieve papers and their metadata."""

import datetime as dt
import hashlib
import logging
import os
import re
import time
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from collections.abc import Callable, Mapping, Sequence
from typing import Any, cast

import httpx

from ...models import Paper, Settings

logger = logging.getLogger("paper_radar.sources")
_cooldowns: dict[str, float] = {}
_SENSITIVE_QUERY = re.compile(r"(?i)([?&](?:api_key|key|token|access_token)=)[^&\s'\"]+")


def _safe_error(error: Exception) -> str:
    """Redact credential-like query parameters from an error message."""
    return _SENSITIVE_QUERY.sub(r"\1[REDACTED]", str(error))


def _since(days: int) -> str:
    """Return the earliest publication date, with one day of overlap.

    :param days: Configured lookback period.
    :returns: The earliest publication date in ISO format.
    """
    return (dt.date.today() - dt.timedelta(days=days + 1)).isoformat()


def fetch_arxiv(
    query: Sequence[str], days: int, limit: int, journals: Sequence[str] | None = None
) -> list[Paper]:
    """Fetch recent papers from the arXiv API.

    :param query: Search terms.
    :param days: Lookback period in days.
    :param limit: Maximum number of API results to request.
    :param journals: Optional journal filter, applied by the caller.
    :returns: Papers published within the lookback period.
    """
    q = " AND ".join(f'all:"{t}"' if " " in t else f"all:{t}" for t in query)
    r = httpx.get("https://export.arxiv.org/api/query", timeout=30, params={
        "search_query": q, "sortBy": "submittedDate", "sortOrder": "descending", "max_results": limit})
    r.raise_for_status()
    ns = {"a": "http://www.w3.org/2005/Atom"}
    out: list[Paper] = []
    cutoff = _since(days)
    for e in ET.fromstring(r.text).findall("a:entry", ns):
        pub = e.findtext("a:published", "", ns)[:10]
        if pub < cutoff: continue
        url = e.findtext("a:id", "", ns)
        out.append(_mk(
            "arxiv", url.rsplit("/abs/", 1)[-1], url=url, source="arxiv", journal="arXiv",
            title=re.sub(r"\s+", " ", e.findtext("a:title", "", ns)).strip(),
            abstract=re.sub(r"\s+", " ", e.findtext("a:summary", "", ns)).strip(),
            authors=", ".join(a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)),
            published=pub, info="abstract", pdf=url.replace("/abs/", "/pdf/")))
    return out

def _openalex_abstract(inv: Mapping[str, Sequence[int]] | None) -> str:
    """Reconstruct an abstract from an OpenAlex inverted index.

    :param inv: Mapping of words to their token positions.
    :returns: The reconstructed abstract, or an empty string if unavailable.
    """
    if not inv:
        return ""
    pos = {i: w for w, idx in inv.items() for i in idx}
    return " ".join(pos[i] for i in sorted(pos))


def fetch_openalex(
    query: Sequence[str], days: int, limit: int, journals: Sequence[str] | None = None
) -> list[Paper]:
    """Fetch recent journal articles from OpenAlex.

    :param query: Search terms.
    :param days: Lookback period in days.
    :param limit: Maximum number of API results to request.
    :param journals: Optional journal-name filters.
    :returns: Matching papers and available metadata.
    """
    flt = f"from_publication_date:{_since(days)},type:article"
    r = httpx.get("https://api.openalex.org/works", timeout=30, params={
        "search": " ".join(query), "filter": flt, "per-page": min(limit, 50), "sort": "publication_date:desc"})
    r.raise_for_status()
    out: list[Paper] = []
    for w in r.json().get("results", []):
        loc = (w.get("primary_location") or {}).get("source") or {}
        journal = loc.get("display_name") or ""
        if journals and not any(j.lower() in journal.lower() for j in journals): continue
        out.append(_mk(
            "oa", w["id"].rsplit("/", 1)[-1], source="openalex", journal=journal,
            title=w.get("title") or "", abstract=_openalex_abstract(w.get("abstract_inverted_index")),
            url=w.get("doi") or w["id"], published=w.get("publication_date", ""),
            authors=", ".join(a["author"]["display_name"] for a in w.get("authorships", [])[:8]),
            info="abstract" if w.get("abstract_inverted_index") else "snippet",
            pdf=(w.get("open_access") or {}).get("oa_url") or "", doi=w.get("doi") or ""))
    return out

def _mk(prefix: str, key: str, **fields: Any) -> Paper:
    """Build a paper record with default metadata fields.

    :param prefix: Source-specific identifier prefix.
    :param key: Source-specific record identifier.
    :param fields: Paper metadata returned by a source.
    :returns: A paper record with standard optional fields populated.
    """
    fields.setdefault("authors", "")
    fields.setdefault("abstract", "")
    fields.setdefault("journal", "")
    fields.setdefault("published", "")
    fields.setdefault("info", "abstract" if fields["abstract"] else "snippet")
    return cast(Paper, {"id": f"{prefix}:{key}", **fields})


def fetch_semanticscholar(
    query: Sequence[str], days: int, limit: int, journals: Sequence[str] | None = None
) -> list[Paper]:
    """Search Semantic Scholar for papers matching the configured query.

    :param query: Search terms.
    :param days: Lookback period in days.
    :param limit: Maximum number of API results to request.
    :param journals: Optional journal filters, applied by the caller.
    :returns: Matching paper records.
    """
    h = {"x-api-key": os.environ["S2_API_KEY"]} if os.environ.get("S2_API_KEY") else {}
    r = httpx.get("https://api.semanticscholar.org/graph/v1/paper/search", timeout=30, headers=h, params={
        "query": " ".join(query), "limit": min(limit, 100), "publicationDateOrYear": _since(days) + ":",
        "fields": "title,abstract,url,venue,authors,publicationDate,externalIds,openAccessPdf"})
    r.raise_for_status()
    return [_mk("s2", p["paperId"], source="semanticscholar", title=p.get("title") or "", url=p.get("url") or "",
                abstract=p.get("abstract") or "", journal=p.get("venue") or "", published=p.get("publicationDate") or "",
                authors=", ".join(a["name"] for a in p.get("authors", [])[:8]),
                pdf=(p.get("openAccessPdf") or {}).get("url", ""), doi=(p.get("externalIds") or {}).get("DOI", ""))
            for p in r.json().get("data", [])]


def fetch_crossref(
    query: Sequence[str], days: int, limit: int, journals: Sequence[str] | None = None
) -> list[Paper]:
    """Search Crossref for recently published journal articles.

    :param query: Search terms.
    :param days: Lookback period in days.
    :param limit: Maximum number of API results to request.
    :param journals: Optional journal filters, applied by the caller.
    :returns: Matching paper records.
    """
    r = httpx.get("https://api.crossref.org/works", timeout=30, params={
        "query": " ".join(query), "rows": min(limit, 50), "sort": "published", "order": "desc",
        "filter": f"from-pub-date:{_since(days)},type:journal-article",
        "mailto": os.environ.get("CONTACT_EMAIL", "")})
    r.raise_for_status()
    out: list[Paper] = []
    for w in r.json()["message"]["items"]:
        d = (w.get("issued", {}).get("date-parts") or [[None]])[0]
        out.append(_mk("cr", w["DOI"], source="crossref", title=(w.get("title") or [""])[0],
            url="https://doi.org/" + w["DOI"], doi=w["DOI"], abstract=re.sub(r"<[^>]+>", " ", w.get("abstract", "")).strip(),
            journal=(w.get("container-title") or [""])[0],
            published="-".join(f"{x:02d}" if i else str(x) for i, x in enumerate(d) if x),
            authors=", ".join(f"{a.get('given','')} {a.get('family','')}".strip() for a in w.get("author", [])[:8])))
    return out


def fetch_pubmed(
    query: Sequence[str], days: int, limit: int, journals: Sequence[str] | None = None
) -> list[Paper]:
    """Search PubMed and retrieve metadata for matching records.

    :param query: Search terms.
    :param days: Lookback period in days.
    :param limit: Maximum number of API results to request.
    :param journals: Optional journal filters, applied by the caller.
    :returns: Matching paper records.
    """
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    s = httpx.get(base + "esearch.fcgi", timeout=30, params={
        "db": "pubmed", "term": " ".join(query), "retmode": "json", "retmax": min(limit, 100), "sort": "pub_date",
        "datetype": "pdat", "mindate": _since(days), "maxdate": dt.date.today().isoformat()})
    s.raise_for_status()
    ids = s.json()["esearchresult"]["idlist"]
    if not ids: return []
    x = httpx.get(base + "efetch.fcgi", timeout=30, params={"db": "pubmed", "id": ",".join(ids), "retmode": "xml"})
    x.raise_for_status()
    out: list[Paper] = []
    for a in ET.fromstring(x.text).findall(".//PubmedArticle"):
        pmid = a.findtext(".//PMID")
        out.append(_mk("pm", pmid, source="pubmed", url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            title="".join(a.find(".//ArticleTitle").itertext()).strip(),
            abstract=" ".join("".join(t.itertext()) for t in a.findall(".//AbstractText")),
            journal=a.findtext(".//Journal/Title") or "",
            published=(a.findtext(".//PubDate/Year") or ""),
            authors=", ".join(f"{p.findtext('ForeName','')} {p.findtext('LastName','')}".strip()
                              for p in a.findall(".//Author")[:8])))
    return out


def fetch_scholar(
    query: Sequence[str], days: int, limit: int, journals: Sequence[str] | None = None
) -> list[Paper]:
    """Search Google Scholar through SerpAPI.

    Google Scholar does not provide an official API; direct scraping is not
    supported. This provider requires the ``SERPAPI_KEY`` environment variable.

    :param query: Search terms.
    :param days: Lookback period in days.
    :param limit: Maximum number of API results to request.
    :param journals: Optional journal filters, applied by the caller.
    :returns: Matching paper records.
    """
    r = httpx.get("https://serpapi.com/search.json", timeout=40, params={
        "engine": "google_scholar", "q": " ".join(query), "scisbd": 1, "as_ylo": dt.date.today().year,
        "num": min(limit, 20), "api_key": os.environ["SERPAPI_KEY"]})
    r.raise_for_status()
    return [_mk("gs", hashlib.md5(p["link"].encode()).hexdigest()[:12], source="scholar", title=p["title"],
                url=p["link"], abstract=p.get("snippet", ""), journal=p.get("publication_info", {}).get("summary", ""),
                published="") for p in r.json().get("organic_results", []) if p.get("link")]


def fetch_web(
    query: Sequence[str], days: int, limit: int, journals: Sequence[str] | None = None
) -> list[Paper]:
    """Search the web through Tavily.

    Results often contain only a title, link, and search snippet. This provider
    requires the ``TAVILY_API_KEY`` environment variable.

    :param query: Search terms.
    :param days: Lookback period in days.
    :param limit: Maximum number of API results to request.
    :param journals: Optional journal filters, applied by the caller.
    :returns: Matching paper records.
    """
    r = httpx.post("https://api.tavily.com/search", timeout=40, json={
        "api_key": os.environ["TAVILY_API_KEY"], "query": "new research paper " + " ".join(query),
        "time_range": "week" if days <= 7 else "month", "max_results": min(limit, 20), "search_depth": "basic"})
    r.raise_for_status()
    return [_mk("web", hashlib.md5(p["url"].encode()).hexdigest()[:12], source="web", title=p["title"], url=p["url"],
                abstract=p.get("content", ""), journal=re.sub(r"^https?://(www\.)?([^/]+).*", r"\2", p["url"]),
                published=(p.get("published_date") or "")[:10]) for p in r.json().get("results", [])]

NEEDS_KEY = {"scholar": "SERPAPI_KEY", "web": "TAVILY_API_KEY"}
FETCHERS: dict[str, Callable[[Sequence[str], int, int, Sequence[str] | None], list[Paper]]] = {
    "arxiv": fetch_arxiv,
    "openalex": fetch_openalex,
    "semanticscholar": fetch_semanticscholar,
    "crossref": fetch_crossref,
    "pubmed": fetch_pubmed,
    "scholar": fetch_scholar,
    "web": fetch_web,
}


def fetch_all(settings: Settings) -> tuple[list[Paper], list[str]]:
    """Fetch papers from all enabled providers.

    Provider failures are returned as warnings and do not stop other providers.

    :param settings: Complete application settings.
    :returns: A tuple containing found papers and provider warnings.
    """
    q = settings["keywords"] or settings["topics"]
    if not q:
        return [], ["No keywords or topics are configured"]
    days = settings["frequency_days"]
    per_source_limit = settings["max_per_run"]
    max_found = min(100, max(1, int(settings["max_found_per_run"])))
    journals = settings["journals"]
    results: list[Paper] = []
    warnings: list[str] = []
    known_ids: set[str] = set()
    known_titles: set[str] = set()
    for name in settings["sources"]:
        remaining_results = max_found - len(results)
        if remaining_results <= 0:
            warnings.append(f"Total paper limit reached ({max_found}); remaining sources skipped")
            logger.info("Total paper limit reached (%d); skipping remaining providers", max_found)
            break
        if name not in FETCHERS: continue
        if name in NEEDS_KEY and not os.environ.get(NEEDS_KEY[name]):
            warnings.append(f"{name}: missing {NEEDS_KEY[name]}, skipped")
            continue
        remaining = _cooldowns.get(name, 0) - time.monotonic()
        if remaining > 0:
            warning = f"{name}: temporarily skipped after rate limiting; retry in about {int(remaining)} seconds"
            warnings.append(warning)
            logger.info("%s", warning)
            continue
        started = time.monotonic()
        request_limit = min(per_source_limit, remaining_results)
        logger.info(
            "Provider %s started (request limit=%d, %d total slots remaining)",
            name,
            request_limit,
            remaining_results,
        )
        try:
            papers = FETCHERS[name](q, days, request_limit, journals)
            if journals and name != "web":
                papers = [
                    paper
                    for paper in papers
                    if any(
                        journal.lower() in paper.get("journal", "").lower()
                        for journal in journals
                    )
                ]
            added = 0
            for paper in papers:
                title = "".join(
                    character for character in paper.get("title", "").lower()
                    if character.isalnum()
                )[:80]
                if not paper.get("title") or paper["id"] in known_ids or title in known_titles:
                    continue
                known_ids.add(paper["id"])
                known_titles.add(title)
                results.append(paper)
                added += 1
                if len(results) >= max_found:
                    break
            _cooldowns.pop(name, None)
            logger.info(
                "Provider %s contributed %d unique papers in %.1fs",
                name,
                added,
                time.monotonic() - started,
            )
            if len(results) >= max_found:
                warning = f"Total paper limit reached ({max_found}); remaining sources skipped"
                warnings.append(warning)
                logger.info("%s", warning)
                break
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                retry_after = e.response.headers.get("Retry-After", "")
                try:
                    cooldown = max(60, int(retry_after))
                except ValueError:
                    try:
                        retry_at = parsedate_to_datetime(retry_after)
                        cooldown = max(60, int((retry_at - dt.datetime.now(retry_at.tzinfo)).total_seconds()))
                    except (TypeError, ValueError, OverflowError):
                        cooldown = 900
                cooldown = min(cooldown, 86400)
                _cooldowns[name] = time.monotonic() + cooldown
                warning = f"{name}: API rate limit (429); skipped and cooling down for {cooldown} seconds"
                if name == "semanticscholar" and not os.environ.get("S2_API_KEY"):
                    warning += "; an S2_API_KEY may provide a higher rate limit"
                warnings.append(warning)
                logger.warning("%s", warning)
            else:
                warnings.append(f"{name}: {_safe_error(e)}")
                logger.exception("Provider %s failed with HTTP %s", name, e.response.status_code)
        except Exception as e:
            warnings.append(f"{name}: {_safe_error(e)}")
            logger.exception("Provider %s failed", name)
    return results, warnings
