"""Run one search from the command line."""

import json

from .service import STATE, run_once
from ...core.logging_config import configure_logging
from ...infrastructure.database import init

configure_logging()
init()
run_once()
print(json.dumps(STATE, ensure_ascii=False, indent=2))
