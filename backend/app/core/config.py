"""Environment-backed application configuration."""

import os

DATABASE_URL = os.environ.get(
    "RADAR_DATABASE_URL",
    "postgresql://paper_radar:paper_radar@localhost:5432/paper_radar",
)
