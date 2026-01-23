"""
PSA Squash Rankings Scraper

A robust Python-based web scraper for fetching professional squash player
rankings from the PSA World Tour.
"""

from .api_scraper import get_rankings

__all__ = [
    "get_rankings",
]