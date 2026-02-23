"""
Centralized configuration for PSA Squash Rankings Scraper.
"""

from pathlib import Path
import os

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


# Use current working directory for output (not package location)
# This allows users to control where files are written
def get_data_dir() -> Path:
    """Get the data directory, defaulting to current working directory."""
    return Path(os.getenv("PSA_DATA_DIR", Path.cwd()))


CHECKPOINT_DIR = get_data_dir() / "checkpoints"
LOG_DIR = get_data_dir() / "logs"
OUTPUT_DIR = get_data_dir() / "output"


def init_dirs() -> None:
    """Create required directories."""
    for directory in [OUTPUT_DIR, LOG_DIR, CHECKPOINT_DIR]:
        directory.mkdir(exist_ok=True)
