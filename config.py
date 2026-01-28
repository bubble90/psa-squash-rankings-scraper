"""
Centralized configuration for PSA Squash Rankings Scraper.

All URLs, timeouts, paths, and constants are defined here
to avoid duplication and make changes easier.
"""
from pathlib import Path

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
]

API_BASE_URL = "https://psa-api.ptsportsuite.com/rankedplayers"
API_TIMEOUT = 10

HTML_BASE_URL = "https://www.psasquashtour.com/rankings/"
HTML_TIMEOUT = 15

PROJECT_ROOT = Path(__file__).parent

CHECKPOINT_DIR = PROJECT_ROOT / "checkpoints"
LOG_DIR = PROJECT_ROOT / "logs"
OUTPUT_DIR = PROJECT_ROOT / "output"

OUTPUT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
CHECKPOINT_DIR.mkdir(exist_ok=True)
