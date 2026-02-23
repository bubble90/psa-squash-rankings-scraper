"""
Command-line interface for PSA Squash Rankings Scraper.
"""

import sys
import argparse
import logging
from typing import Literal, cast

from psa_squash_rankings.api_scraper import get_rankings
from psa_squash_rankings.html_scraper import scrape_rankings_html
from psa_squash_rankings.exporter import export_to_csv
from psa_squash_rankings.logger import get_logger
from psa_squash_rankings.config import init_dirs

logger = get_logger(__name__)


def main() -> int:
    """
    Main entry point with command-line argument support.
    Returns exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        prog="psa-scrape", description="PSA Squash Rankings Scraper"
    )
    parser.add_argument(
        "--gender",
        choices=["male", "female", "both"],
        default="both",
        help="Gender to scrape (default: both)",
    )
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Number of results per page (default: 100)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of pages to fetch (default: all)",
    )
    parser.add_argument(
        "--no-resume", action="store_true", help="Start fresh, ignore checkpoints"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    args = parser.parse_args()

    # Initialize directories
    init_dirs()

    logging.getLogger().setLevel(getattr(logging, args.log_level))
    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(getattr(logging, args.log_level))

    logger.info("=" * 60)
    logger.info("PSA Squash Rankings Scraper - Starting")
    logger.info("=" * 60)
    logger.info(
        f"Configuration: gender={args.gender}, page_size={args.page_size}, "
        f"max_pages={args.max_pages}, resume={not args.no_resume}"
    )

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


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.warning("\nScraping interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
