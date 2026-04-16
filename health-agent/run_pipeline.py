#!/usr/bin/env python3
"""
Scheduled pipeline script — run by PythonAnywhere's task scheduler daily.

Checks if today is a posting day (Mon/Wed/Fri by default), then runs the
full content generation pipeline: scrape → select → generate → design → queue.

PythonAnywhere task command:
  /home/<username>/.virtualenvs/health-agent/bin/python /home/<username>/health-agent/run_pipeline.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Project root on path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

import config
from utils.helpers import configure_logging

configure_logging()

import logging
logger = logging.getLogger(__name__)

# ── Day-of-week check ─────────────────────────────────────────────────────────
DAY_MAP = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
schedule_days = [d.strip().lower() for d in config.SCHEDULE_DAYS.split(",")]
allowed_weekdays = [DAY_MAP[d] for d in schedule_days if d in DAY_MAP]

today_weekday = datetime.now().weekday()
today_name = datetime.now().strftime("%A")

if today_weekday not in allowed_weekdays:
    logger.info("Today is %s — not a posting day. Skipping.", today_name)
    sys.exit(0)

logger.info("Today is %s — running content pipeline.", today_name)

# ── Run the pipeline ──────────────────────────────────────────────────────────
from scheduler import run_full_pipeline

run_full_pipeline()
