"""
Command-line interface for PSA Squash Rankings Scraper.
"""

import sys
import argparse
import logging
import pandas as pd
from typing import Literal, cast

from psa_squash_rankings.api_scraper import get_rankings
from psa_squash_rankings.html_scraper import scrape_rankings_html
from psa_squash_rankings.squashinfo_scraper import (
    get_recent_tournaments,
    get_tournament_matches,
    get_player_recent_matches,
    get_player_recent_tournaments,
    get_player_biography,
)
from psa_squash_rankings.exporter import export_to_csv
from psa_squash_rankings.logger import get_logger
from psa_squash_rankings.config import init_dirs, OUTPUT_DIR

logger = get_logger(__name__)


def _run_rankings(args) -> int:
    """Scrape PSA player rankings."""
    gender_arg = cast(Literal["male", "female", "both"], args.gender)
    genders = ["male", "female"] if gender_arg == "both" else [gender_arg]

    success_count = 0
    failure_count = 0

    for gender in genders:
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"Processing {gender.capitalize()} Rankings")
        logger.info("=" * 60)

        try:
            gender_literal = cast(Literal["male", "female"], gender)
            result = get_rankings(
                gender=gender_literal,
                page_size=args.page_size,
                max_pages=args.max_pages,
                resume=not args.no_resume,
            )

            output_file = f"psa_rankings_{gender}.csv"
            export_to_csv(result, output_file)

            logger.info(f"Successfully scraped {len(result)} {gender} players")
            logger.info(f"Data exported to: {output_file}")
            success_count += 1

        except Exception as e:
            logger.error(f"API failed for {gender}: {e}")
            logger.info(f"Attempting HTML fallback for {gender}...")

            try:
                fallback_result = scrape_rankings_html()
                fallback_file = f"psa_rankings_{gender}_fallback.csv"
                export_to_csv(fallback_result, fallback_file)
                logger.info(f"Fallback successful: {fallback_file}")
                success_count += 1

            except Exception as html_err:
                logger.error(f"Critical Error: Both sources failed for {gender}")
                logger.exception(f"Error details: {html_err}")
                failure_count += 1

    logger.info("")
    logger.info("=" * 60)
    logger.info("Scraping complete!")
    logger.info("=" * 60)
    logger.info(f"Summary: {success_count} successful, {failure_count} failed")

    return 0 if failure_count == 0 else 1


def _run_tournaments(args) -> int:
    """Scrape recent tournament listings from squashinfo.com."""
    logger.info("=" * 60)
    logger.info("Fetching recent tournaments from squashinfo.com")
    logger.info("=" * 60)

    try:
        tournaments = get_recent_tournaments(max_pages=args.max_pages)
        if not tournaments:
            logger.warning("No tournaments found")
            return 1

        import pandas as pd

        output_path = OUTPUT_DIR / "squashinfo_tournaments.csv"
        pd.DataFrame(tournaments).to_csv(output_path, index=False)

        logger.info(f"Fetched {len(tournaments)} tournaments")
        logger.info("Data exported to: squashinfo_tournaments.csv")
        return 0

    except Exception as e:
        logger.exception(f"Failed to fetch tournaments: {e}")
        return 1


def _run_matches(args) -> int:
    """Scrape match results for a specific tournament from squashinfo.com."""
    logger.info("=" * 60)
    logger.info(f"Fetching matches for event {args.event_id} ({args.slug})")
    logger.info("=" * 60)

    try:
        matches = get_tournament_matches(args.event_id, args.slug)
        if not matches:
            logger.warning(f"No matches found for event {args.event_id}")
            return 1

        output_path = OUTPUT_DIR / f"squashinfo_matches_{args.event_id}.csv"
        pd.DataFrame(matches).to_csv(output_path, index=False)

        logger.info(f"Fetched {len(matches)} matches")
        logger.info(f"Data exported to: squashinfo_matches_{args.event_id}.csv")
        return 0

    except Exception as e:
        logger.exception(f"Failed to fetch matches: {e}")
        return 1


def _run_player_history(args) -> int:
    """Scrape a player's recent matches and tournaments from squashinfo.com."""
    logger.info("=" * 60)
    logger.info(f"Fetching player history for player {args.player_id} ({args.slug})")
    logger.info("=" * 60)

    exit_code = 0

    try:
        matches = get_player_recent_matches(args.player_id, args.slug)
        if matches:
            output_path = OUTPUT_DIR / f"squashinfo_player_{args.player_id}_matches.csv"
            pd.DataFrame(matches).to_csv(output_path, index=False)
            logger.info(f"Fetched {len(matches)} recent matches")
            logger.info(
                f"Data exported to: squashinfo_player_{args.player_id}_matches.csv"
            )
        else:
            logger.warning("No recent matches found")
    except Exception as e:
        logger.exception(f"Failed to fetch recent matches: {e}")
        exit_code = 1

    try:
        tournaments = get_player_recent_tournaments(args.player_id, args.slug)
        if tournaments:
            output_path = (
                OUTPUT_DIR / f"squashinfo_player_{args.player_id}_tournaments.csv"
            )
            pd.DataFrame(tournaments).to_csv(output_path, index=False)
            logger.info(f"Fetched {len(tournaments)} recent tournaments")
            logger.info(
                f"Data exported to: squashinfo_player_{args.player_id}_tournaments.csv"
            )
        else:
            logger.warning("No recent tournaments found")
    except Exception as e:
        logger.exception(f"Failed to fetch recent tournaments: {e}")
        exit_code = 1

    return exit_code


def _run_player_bio(args) -> int:
    """Scrape a player's biography from squashinfo.com."""
    logger.info("=" * 60)
    logger.info(f"Fetching biography for player {args.player_id} ({args.slug})")
    logger.info("=" * 60)

    try:
        bio = get_player_biography(args.player_id, args.slug)
        if bio is None:
            logger.warning(f"No biography found for player {args.player_id}")
            return 1

        output_path = OUTPUT_DIR / f"squashinfo_player_{args.player_id}_biography.csv"
        pd.DataFrame([bio]).to_csv(output_path, index=False)

        logger.info(f"Fetched biography for {bio['name']}")
        logger.info(
            f"Data exported to: squashinfo_player_{args.player_id}_biography.csv"
        )
        return 0

    except Exception as e:
        logger.exception(f"Failed to fetch biography: {e}")
        return 1


def main() -> int:
    """
    Main entry point with subcommand support.

    Subcommands:
      rankings    Scrape PSA player rankings (default)
      tournaments Scrape recent tournament list from squashinfo.com
      matches     Scrape match results for a tournament from squashinfo.com

    Returns exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        prog="psa-scrape", description="PSA Squash Rankings Scraper"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    subparsers = parser.add_subparsers(dest="command", help="Subcommand to run")

    # rankings subcommand (default behaviour)
    rankings_parser = subparsers.add_parser(
        "rankings", help="Scrape PSA player rankings"
    )
    rankings_parser.add_argument(
        "--gender",
        choices=["male", "female", "both"],
        default="both",
        help="Gender to scrape (default: both)",
    )
    rankings_parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Number of results per page (default: 100)",
    )
    rankings_parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of pages to fetch (default: all)",
    )
    rankings_parser.add_argument(
        "--no-resume", action="store_true", help="Start fresh, ignore checkpoints"
    )

    # tournaments subcommand
    tournaments_parser = subparsers.add_parser(
        "tournaments", help="Scrape recent tournament list from squashinfo.com"
    )
    tournaments_parser.add_argument(
        "--max-pages",
        type=int,
        default=1,
        help="Number of pages to fetch (~20 tournaments/page, default: 1)",
    )

    # matches subcommand
    matches_parser = subparsers.add_parser(
        "matches", help="Scrape match results for a tournament from squashinfo.com"
    )
    matches_parser.add_argument(
        "--event-id",
        type=int,
        required=True,
        help="Tournament event ID (e.g. 11593)",
    )
    matches_parser.add_argument(
        "--slug",
        required=True,
        help="Tournament URL slug (e.g. mens-australian-open-2026)",
    )

    # player-history subcommand
    player_parser = subparsers.add_parser(
        "player-history",
        help="Scrape a player's recent matches and tournaments from squashinfo.com",
    )
    player_parser.add_argument(
        "--player-id",
        type=int,
        required=True,
        help="Player ID (e.g. 5974)",
    )
    player_parser.add_argument(
        "--slug",
        required=True,
        help="Player URL slug (e.g. paul-coll)",
    )

    # player-bio subcommand
    bio_parser = subparsers.add_parser(
        "player-bio",
        help="Scrape a player's biography from squashinfo.com",
    )
    bio_parser.add_argument(
        "--player-id",
        type=int,
        required=True,
        help="Player ID (e.g. 5974)",
    )
    bio_parser.add_argument(
        "--slug",
        required=True,
        help="Player URL slug (e.g. paul-coll)",
    )

    args = parser.parse_args()

    # Default to rankings when no subcommand given (backwards compat)
    if args.command is None:
        args.command = "rankings"
        args.gender = "both"
        args.page_size = 100
        args.max_pages = None
        args.no_resume = False

    init_dirs()

    logging.getLogger().setLevel(getattr(logging, args.log_level))
    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(getattr(logging, args.log_level))

    logger.info("=" * 60)
    logger.info("PSA Squash Scraper - Starting")
    logger.info("=" * 60)

    if args.command == "rankings":
        return _run_rankings(args)
    elif args.command == "tournaments":
        return _run_tournaments(args)
    elif args.command == "matches":
        return _run_matches(args)
    elif args.command == "player-history":
        return _run_player_history(args)
    elif args.command == "player-bio":
        return _run_player_bio(args)

    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.warning("\nScraping interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
