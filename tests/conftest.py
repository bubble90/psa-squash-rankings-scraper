"""
Pytest configuration file.

Adds the parent directory to sys.path so that test files can import
the scraper modules directly without needing package installation.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
