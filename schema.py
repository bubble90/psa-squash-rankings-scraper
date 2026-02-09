"""
Schema definitions for PSA Squash Rankings Scraper.

Defines distinct types for API and HTML scraper outputs,
making it explicit when consumers are working with degraded data.
"""

from typing import TypedDict, Optional, Literal


class ApiPlayerRecord(TypedDict):
    """
    Complete player record from API scraper.

    Contains all available fields including player ID and biographical data.
    This is the preferred data source.
    """

    rank: int
    player: str
    id: int
    tournaments: int
    points: int
    height_cm: Optional[int]
    weight_kg: Optional[int]
    birthdate: Optional[str]
    country: Optional[str]
    source: Literal["api"]


class HtmlPlayerRecord(TypedDict):
    """
    Limited player record from HTML scraper (fallback only).

    WARNING: This is a degraded data source that lacks:
    - Player ID (cannot join with other datasets)
    - Biographical data (height, weight, birthdate, country)

    Use only when API is unavailable.
    """

    rank: int
    player: str
    tournaments: int
    points: int
    source: Literal["html"]


ScraperResult = list[ApiPlayerRecord] | list[HtmlPlayerRecord]


def is_api_result(result: ScraperResult) -> bool:
    """
    Type guard to check if result is from API scraper.

    Example:
        result = get_rankings("male")
        if is_api_result(result):
            # Safe to access 'id' field
            player_id = result[0]['id']
    """
    return len(result) > 0 and result[0].get("source") == "api"


def is_html_result(result: ScraperResult) -> bool:
    """
    Type guard to check if result is from HTML scraper (fallback).

    Example:
        result = get_rankings("male")
        if is_html_result(result):
            # Degraded data - no ID field available
            logger.warning("Using fallback data without player IDs")
    """
    return len(result) > 0 and result[0].get("source") == "html"
