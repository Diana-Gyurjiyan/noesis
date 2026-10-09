"""FastAPI application composition for Noesis.

Run the development server with ``uv run uvicorn app.main:app --reload`` from
the backend folder.
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .capabilities.papers.router import router as papers_router
from .capabilities.search.router import router as search_router
from .capabilities.settings.router import router as settings_router
from .capabilities.search.scheduler import start as start_scheduler
from .capabilities.search.scheduler import stop as stop_scheduler
from .core.logging_config import configure_logging
from .infrastructure import database

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start and stop the periodic scheduler with the application lifespan."""
    database.init()
    start_scheduler()
    logging.getLogger("paper_radar.api").info("Noesis API started")
    try:
        yield
    finally:
        stop_scheduler()
        logging.getLogger("paper_radar.api").info("API stopped; scheduler shut down")


app = FastAPI(title="Noesis", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(settings_router)
app.include_router(papers_router)
app.include_router(search_router)
