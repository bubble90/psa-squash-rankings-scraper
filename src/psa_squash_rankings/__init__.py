"""
PSA Squash Rankings Scraper.

A Python library for fetching professional squash player rankings
from the PSA World Tour, and tournament/match data from squashinfo.com.

Example:
    from psa_squash_rankings import get_rankings, is_api_result

    players = get_rankings("male", page_size=100)
    if is_api_result(players):
        print(f"Got {len(players)} players with full data")

    from psa_squash_rankings import get_recent_tournaments, get_tournament_matches

    tournaments = get_recent_tournaments(max_pages=1)
    matches = get_tournament_matches(11593, "mens-australian-open-2026")
"""

from psa_squash_rankings.api_scraper import get_rankings, get_player_bio
from psa_squash_rankings.html_scraper import scrape_rankings_html
from psa_squash_rankings.exporter import export_to_csv
from psa_squash_rankings.squashinfo_scraper import (
    get_recent_tournaments,
    get_tournament_matches,
    get_player_recent_matches,
    get_player_recent_tournaments,
)
from psa_squash_rankings.validator import (
    validate_player_match_record,
    validate_player_tournament_record,
    validate_player_data,
    validate_psa_player_bio_record,
    validate_psa_player_bio,
)
from psa_squash_rankings.schema import (
    ApiPlayerRecord,
    HtmlPlayerRecord,
    ScraperResult,
    TournamentRecord,
    MatchRecord,
    PlayerRecentMatchRecord,
    PlayerRecentTournamentRecord,
    PsaPlayerBioRecord,
    is_api_result,
    is_html_result,
)

__version__ = "1.0.0"
__all__ = [
    "get_rankings",
    "get_player_bio",
    "scrape_rankings_html",
    "export_to_csv",
    "get_recent_tournaments",
    "get_tournament_matches",
    "get_player_recent_matches",
    "get_player_recent_tournaments",
    "ApiPlayerRecord",
    "HtmlPlayerRecord",
    "ScraperResult",
    "TournamentRecord",
    "MatchRecord",
    "PlayerRecentMatchRecord",
    "PlayerRecentTournamentRecord",
    "PsaPlayerBioRecord",
    "is_api_result",
    "is_html_result",
    "validate_player_match_record",
    "validate_player_tournament_record",
    "validate_player_data",
    "validate_psa_player_bio_record",
    "validate_psa_player_bio",
    "__version__",
]
