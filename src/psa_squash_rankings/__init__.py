"""
PSA Squash Rankings Scraper.

A Python library for fetching professional squash player rankings
from the PSA World Tour.

Example:
    from psa_squash_rankings import get_rankings, is_api_result

    players = get_rankings("male", page_size=100)
    if is_api_result(players):
        print(f"Got {len(players)} players with full data")
"""

from psa_squash_rankings.api_scraper import get_rankings
from psa_squash_rankings.html_scraper import scrape_rankings_html
from psa_squash_rankings.exporter import export_to_csv
from psa_squash_rankings.schema import (
    ApiPlayerRecord,
    HtmlPlayerRecord,
    ScraperResult,
    is_api_result,
    is_html_result,
)

__version__ = "1.0.0"
__all__ = [
    "get_rankings",
    "scrape_rankings_html",
    "export_to_csv",
    "ApiPlayerRecord",
    "HtmlPlayerRecord",
    "ScraperResult",
    "is_api_result",
    "is_html_result",
    "__version__",
]
