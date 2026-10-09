"""Download open-access PDFs and extract relevant full-text sections."""

import io
import logging
import os
import re

import httpx
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from ...models import Paper

logger = logging.getLogger("paper_radar.fulltext")

MAX_BYTES = 15 * 1024 * 1024
HEAD = re.compile(r"^\s*(?:\d+(?:\.\d+)*\.?\s+)?(conclusions?|limitations?|future work|future directions|"
                  r"discussion|concluding remarks|outlook)\b.*$", re.I | re.M)

def pdf_url(paper: Paper) -> str:
    """Find a PDF URL from metadata or the Unpaywall API.

    :param paper: Paper metadata, including optional PDF URL and DOI.
    :returns: A direct PDF URL, or an empty string when none is available.
    """
    if paper.get("pdf"):
        return paper.get("pdf", "")
    doi = (paper.get("doi") or "").replace("https://doi.org/", "")
    email = os.environ.get("CONTACT_EMAIL")
    if doi and email:
        try:
            r = httpx.get(f"https://api.unpaywall.org/v2/{doi}", params={"email": email}, timeout=15)
            if r.status_code == 200:
                return (r.json().get("best_oa_location") or {}).get("url_for_pdf") or ""
        except (httpx.HTTPError, ValueError):
            logger.warning("Could not resolve an open-access PDF for DOI %s", doi, exc_info=True)
    return ""


def download(url: str) -> bytes | None:
    """Download a PDF while enforcing the configured size limit.

    :param url: Candidate PDF URL.
    :returns: PDF bytes, or ``None`` for non-PDF content or oversized files.
    :raises httpx.HTTPError: If the remote server returns an error.
    """
    buf = b""
    with httpx.stream("GET", url, timeout=30, follow_redirects=True, headers={"User-Agent": "paper-radar/0.2"}) as r:
        r.raise_for_status()
        for chunk in r.iter_bytes():
            buf += chunk
            if len(buf) > MAX_BYTES: return None
    return buf if buf[:5] == b"%PDF-" else None


def pdf_text(data: bytes, max_pages: int = 40) -> str:
    """Extract text from the first pages of a PDF.

    :param data: PDF file contents.
    :param max_pages: Maximum number of pages to extract.
    :returns: Extracted page text joined by newlines.
    """
    return "\n".join((pg.extract_text() or "") for pg in PdfReader(io.BytesIO(data)).pages[:max_pages])


def sections(text: str, cap: int = 6000) -> str:
    """Select the discussion, conclusion, or final section of extracted text.

    :param text: Full extracted PDF text.
    :param cap: Maximum excerpt length in characters.
    :returns: Relevant excerpt, limited to ``cap`` characters.
    """
    m = re.search(r"^\s*(?:\d+\.?\s+)?(references|bibliography)\s*$", text, re.I | re.M)
    body = text[:m.start()] if m and m.start() > len(text) * 0.3 else text
    late = [h for h in HEAD.finditer(body) if h.start() > len(body) * 0.4 and len(h.group(0).strip()) < 80]
    return (body[late[0].start():late[0].start() + cap] if late else body[-cap:]).strip()


def excerpt(paper: Paper) -> str | None:
    """Download a paper's PDF and return a useful excerpt when available.

    :param paper: Paper metadata with a direct PDF URL or DOI.
    :returns: A relevant text excerpt, or ``None`` when no usable text exists.
    """
    try:
        url = pdf_url(paper)
        data = download(url) if url else None
        text = pdf_text(data) if data else ""
        return sections(text) if len(text) > 2000 else None
    except (httpx.HTTPError, PdfReadError, OSError, ValueError):
        logger.exception("Could not extract full text for paper %s", paper.get("id", "unknown"))
        return None
