"""Periodic scheduler for automatic search runs."""

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from .service import run_once
from ..settings.service import get_settings

logger = logging.getLogger("paper_radar.scheduler")
scheduler = BackgroundScheduler()


def reschedule() -> None:
    """Replace the periodic search job using the saved run frequency."""
    scheduler.remove_all_jobs()
    frequency_days = max(1, int(get_settings()["frequency_days"]))
    scheduler.add_job(
        run_once,
        "interval",
        days=frequency_days,
        id="radar",
        replace_existing=True,
    )
    logger.info("Scheduled paper search every %d day(s)", frequency_days)


def start() -> None:
    """Start the scheduler and install its recurring search job."""
    if not scheduler.running:
        scheduler.start()
    reschedule()


def stop() -> None:
    """Stop the scheduler when the API shuts down."""
    if scheduler.running:
        scheduler.shutdown()
