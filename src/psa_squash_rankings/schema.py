"""
Schema definitions for PSA Squash Rankings Scraper.

Defines distinct types for API and HTML scraper outputs,
making it explicit when consumers are working with degraded data.
"""

from typing import TypedDict, Optional, Literal, Union


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
    picture_url: Optional[str]
    mugshot_url: Optional[str]
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
    mugshot_url: Optional[str]
    source: Literal["html"]


ScraperResult = Union[list[ApiPlayerRecord], list[HtmlPlayerRecord]]


class TournamentRecord(TypedDict):
    """
    Tournament record from squashinfo.com.

    Contains metadata for a PSA squash tournament.
    """

    id: int
    name: str
    gender: Optional[str]  # "M", "W", or None
    tier: str
    location: str
    date: str
    url: str
    source: Literal["squashinfo"]


class MatchRecord(TypedDict):
    """
    Match record from squashinfo.com.

    Contains player info, scores, and result for a single match.
    """

    match_id: int
    tournament_id: int
    tournament_name: str
    round: str
    player1_name: str
    player1_id: Optional[int]
    player1_country: Optional[str]
    player1_seeding: Optional[str]
    player2_name: str
    player2_id: Optional[int]
    player2_country: Optional[str]
    player2_seeding: Optional[str]
    winner: Optional[str]  # player1_name if completed, None if not yet played
    scores: Optional[str]  # e.g., "11-5, 11-4, 11-5"
    duration_minutes: Optional[int]
    source: Literal["squashinfo"]


class PlayerRecentMatchRecord(TypedDict):
    """
    A single match from a player's recent match history on squashinfo.com.

    Scraped from the player profile page (/player/{id}-{slug}).
    Each row includes tournament context, round, opponent, and result.
    """

    player_id: int
    tournament_id: Optional[int]
    tournament_name: str
    round: str
    opponent_name: str
    opponent_id: Optional[int]
    opponent_country: Optional[str]
    result: str  # "W", "L", or "" for upcoming/incomplete
    scores: Optional[str]
    duration_minutes: Optional[int]
    date: Optional[str]
    source: Literal["squashinfo"]


class PlayerRecentTournamentRecord(TypedDict):
    """
    A tournament entry from a player's recent tournament history on squashinfo.com.

    Scraped from the player profile page (/player/{id}-{slug}).
    Shows the deepest round reached at each event.
    """

    player_id: int
    tournament_id: Optional[int]
    tournament_name: str
    tier: Optional[str]
    location: Optional[str]
    date: Optional[str]
    round_reached: str
    source: Literal["squashinfo"]



class PsaPlayerBioRecord(TypedDict):
    """
    Player biography fetched from the PSA API (/player/{id}).

    Contains the full biographical profile for a single player including
    their written bio, physical stats, coaching staff, and social links.
    The bio field is plain text with HTML tags stripped.
    """

    player_id: int
    name: str
    country: Optional[str]
    flag_url: Optional[str]
    birthdate: Optional[str]
    birthplace: Optional[str]
    height_cm: Optional[int]
    weight_kg: Optional[int]
    coach: Optional[str]
    residence: Optional[str]
    bio: Optional[str]
    picture_url: Optional[str]
    mugshot_url: Optional[str]
    twitter: Optional[str]
    facebook: Optional[str]
    source: Literal["api"]


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
