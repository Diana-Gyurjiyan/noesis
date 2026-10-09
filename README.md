# Noesis

*Beyond finding. Towards understanding.*

Noesis (Greek: νόησις) means intellectual understanding: the activity of the mind through which something is understood. The app helps researchers understand what discovered papers mean for their work.

Noesis periodically searches research sources, deduplicates new papers by ID and title, analyzes their
relevance to your research with an LLM, and stores the results in PostgreSQL. Paper summaries are available in
Dutch or English.

## Getting started

Install dependencies and start PostgreSQL in Docker:

    make setup
    make db-up

Start the backend and frontend together (this starts PostgreSQL in Docker and uses that database):

    make dev

Open http://localhost:5173. The backend runs at http://localhost:8000. Stop both servers with Ctrl+C.
Set any required LLM API keys in your shell before running `make dev`. To start the services separately, run
`cd backend && RADAR_DATABASE_URL=postgresql://paper_radar:paper_radar@localhost:5432/paper_radar uv run uvicorn app.main:app --reload`
and `cd frontend && npm run dev`. Run `make db-down` to stop PostgreSQL; its named Docker volume preserves data.
The backend uses only PostgreSQL. If you still need to import an old SQLite database, do so explicitly once with
`make db-import-sqlite`; normal startup never reads from SQLite.

The Docker Compose file uses development-only credentials. Change the database name, user, and password before
using this setup outside a local development environment.

Each search run fetches at most 20 unique papers and analyzes at most five papers by default; adjust both limits
independently in Settings. Rotating backend logs
are written to `backend/logs/paper-radar.log`; follow them in real time with `make logs`. Search logs describe
each source request, analysis progress, saved result, and failure. `make dev` suppresses routine HTTP polling
logs so these progress messages remain easy to follow; the frontend also shows the current search stage and
paper being analyzed.

## Local LLM (no API key required)

Install and start [Ollama](https://ollama.com/download), download a model, and verify that it is available locally:

    ollama pull qwen3:8b
    ollama list

Ollama must be available at `http://localhost:11434` while the backend is running. It is the default provider,
and you can choose a different provider and model under Settings. The default model is `qwen3:8b`; smaller
models may be suitable for computers with less memory. Ollama is prompted to return JSON; malformed output is
normalized and retried once.

For LM Studio, llama.cpp, or vLLM, select the `openai` provider and set `OPENAI_BASE_URL`, for example
`http://localhost:1234/v1`, and `OPENAI_API_KEY`. Hosted Anthropic and OpenAI providers require their respective
API keys; a Claude subscription does not include API access.

## Full text and future work

Papers scoring at least `fulltext_min_score` (default 5) receive a second analysis pass. Noesis attempts to
retrieve a PDF from arXiv, an open-access URL, or Unpaywall (set `CONTACT_EMAIL`), then sends the discussion,
limitations, and conclusion excerpt to the LLM. If no open PDF is available, analysis uses the abstract and
leaves `future_work` empty when it is not mentioned. Disable this feature with `fulltext=false` in Settings.

## Search sources

Available without API keys: arXiv, OpenAlex, Semantic Scholar, PubMed, and Crossref. Optional keyed sources are
`scholar` (Google Scholar through SerpAPI; `SERPAPI_KEY`) and `web` (Tavily; `TAVILY_API_KEY`), which often
returns only titles, links, and snippets. Sources that lack a required key are skipped and reported by
`/api/status`. Optional: `S2_API_KEY` for a higher Semantic Scholar rate limit and `CONTACT_EMAIL` for Crossref.
Direct scraping of Google Scholar is intentionally not used because it is blocked and disallowed by its terms.

## API

Analysis uses the title and abstract; when only a search snippet is available (such as from web search or Google
Scholar), the relevance score is capped at 6 and `future_work` is left empty.

Endpoints: `GET`/`PUT /api/settings`, `POST /api/run`, `GET /api/status`, and `GET /api/papers?min_score=5`.
