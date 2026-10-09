# Handoff

The backend is organized as the `backend/app` Python package. FastAPI routes and services are grouped by
capability under `backend/app/capabilities/`; shared database and logging adapters live in `infrastructure/`
and `core/`. Start it with `uv run uvicorn app.main:app --reload` from `backend/`.

Implemented: backend using uv, search sources (arXiv, OpenAlex, Semantic Scholar, PubMed, Crossref, SerpAPI, and
Tavily), Ollama JSON mode with output normalization and retry, and a full-text second pass using pypdf.
PostgreSQL runs in Docker Compose; `make dev` starts and uses the Docker database. Import an old
`backend/radar.db` SQLite database explicitly with `make db-import-sqlite`.

Previously tested with a mock LLM: dependency sync, API import, deduplication, missing API-key warnings, PDF
download and section extraction, second-pass score threshold, and malformed LLM output normalization.

Not tested against live services: search APIs, hosted or local LLMs, Unpaywall, and arXiv PDFs with two-column
layouts (pypdf may extract these in a confusing order; inspect excerpts).

Frontend: React + TypeScript + Vite in `frontend/src`, with Dutch/English UI, source selection, full-text
toggle, and demo mode. The default LLM is local Ollama (`qwen3:8b`); install Ollama and pull the model before
running searches. arXiv uses HTTPS; anonymous Semantic Scholar requests may be rate-limited (HTTP 429).

Search runs fetch at most 20 unique papers and analyze at most five by default; both limits are configurable.
Source HTTP 429 responses trigger a cooldown. Backend logs
are written to `backend/logs/`.

Potential next steps: user feedback signals included in prompts, seed papers and citation tracking through
OpenAlex, scheduled digests, and a Claude CLI provider (check its terms first).
