"""
Main scraper runner with explicit fallback typing.

This script makes it clear to consumers when they are working with
degraded HTML fallback data versus complete API data.
"""

import sys
import argparse
import logging
from typing import Literal
from api_scraper import get_rankings
from html_scraper import scrape_rankings_html
from exporter import export_to_csv
from logger import get_logger
from schema import ScraperResult, is_api_result, is_html_result
from config import init_dirs


def configure_log_level(log_level: str) -> None:
    """
    Configure logging level for application loggers only.

    Parameters:
    - log_level: Logging level string (DEBUG, INFO, WARNING, ERROR)
    """
    level = getattr(logging, log_level.upper())

    app_logger_names = [
        __name__,
        "api_scraper",
        "html_scraper",
        "data_parser",
        "exporter",
        "logger",
        "validator",
    ]

    for logger_name in app_logger_names:
        app_logger = logging.getLogger(logger_name)
        app_logger.setLevel(level)

        for handler in app_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(level)


def scrape_gender(
    gender: Literal["male", "female"],
    page_size: int,
    max_pages: int | None,
    resume: bool,
) -> tuple[ScraperResult, bool]:
    """
    Scrape rankings for a specific gender with explicit fallback handling.

    Returns:
    - tuple[ScraperResult, bool]: (data, is_fallback)
        - data: Either list[ApiPlayerRecord] or list[HtmlPlayerRecord]
        - is_fallback: True if HTML fallback was used

    Raises:
    - Exception: If both API and fallback fail
    """
    logger = get_logger(__name__)

    try:
        logger.info(f"Attempting API scrape for {gender} rankings...")
        data = get_rankings(
            gender=gender,
            page_size=page_size,
            max_pages=max_pages,
            resume=resume,
        )

        logger.info(
            f"✓ API scrape successful: {len(data)} {gender} players with complete data"
        )
        return data, False

    except Exception as api_error:
        logger.error(f"✗ API scrape failed for {gender}: {api_error}")

        if gender == "male":
            logger.warning("=" * 60)
            logger.warning("FALLING BACK TO HTML SCRAPER")
            logger.warning(
                "WARNING: HTML data is DEGRADED - missing player IDs and biographical info"
            )
            logger.warning("=" * 60)

            try:
                data = scrape_rankings_html()
                logger.info(
                    f"✓ HTML fallback successful: {len(data)} {gender} players (degraded data)"
                )
                return data, True

            except Exception as html_error:
                logger.error(f"✗ HTML fallback also failed for {gender}: {html_error}")
                raise Exception(
                    f"Both API and HTML scrapers failed for {gender}. "
                    f"API error: {api_error}. HTML error: {html_error}"
                )
        else:
            logger.error(
                f"No HTML fallback available for {gender} (HTML scraper only supports male)"
            )
            raise Exception(
                f"API scraper failed for {gender} and no fallback available: {api_error}"
            )


def main() -> None:
    """
    Main entry point with command-line argument support.

    Tries API with pagination for both genders, falls back to HTML if needed.
    Explicitly logs data quality (complete vs degraded) for each result.
    """
    init_dirs()

    logger = get_logger(__name__)

    parser = argparse.ArgumentParser(description="PSA Squash Rankings Scraper")
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

    args = parser.parse_args()

    configure_log_level(args.log_level)

    logger.info("=" * 60)
    logger.info("PSA Squash Rankings Scraper - Starting")
    logger.info("=" * 60)
    logger.info(
        f"Configuration: gender={args.gender}, page_size={args.page_size}, "
        f"max_pages={args.max_pages}, resume={not args.no_resume}"
    )

    if args.gender == "both":
        genders: list[Literal["male", "female"]] = ["male", "female"]
    else:
        genders: list[Literal["male", "female"]] = [args.gender]

    success_count = 0
    failure_count = 0
    fallback_count = 0

    for gender in genders:
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"Processing {gender.capitalize()} Rankings")
        logger.info("=" * 60)

        try:
            data, is_fallback = scrape_gender(
                gender=gender,
                page_size=args.page_size,
                max_pages=args.max_pages,
                resume=not args.no_resume,
            )

            if is_fallback:
                output_file = f"psa_rankings_{gender}_fallback.csv"
                fallback_count += 1
            else:
                output_file = f"psa_rankings_{gender}.csv"

            export_to_csv(data, output_file)

            if is_api_result(data):
                logger.info(
                    f"✓ Successfully scraped {len(data)} {gender} players with COMPLETE data "
                    f"(includes player IDs and biographical info)"
                )
            elif is_html_result(data):
                logger.warning(
                    f"⚠ Successfully scraped {len(data)} {gender} players with DEGRADED data "
                    f"(missing player IDs and biographical info)"
                )

            logger.info(f"Data exported to: {output_file}")
            success_count += 1

        except Exception as e:
            logger.error(f"✗ Failed to scrape {gender} rankings: {e}")
            logger.exception("Full error traceback:")
            failure_count += 1

    logger.info("")
    logger.info("=" * 60)
    logger.info("Scraping complete!")
    logger.info("=" * 60)
    logger.info(f"Summary: {success_count} successful, {failure_count} failed")

    if fallback_count > 0:
        logger.warning(
            f"⚠ WARNING: {fallback_count} result(s) used HTML fallback - "
            f"data is DEGRADED (missing IDs and biographical info)"
        )
        logger.warning(
            "For production use, investigate why the API scraper failed and use complete API data."
        )

    sys.exit(0 if failure_count == 0 else 1)


if __name__ == "__main__":
    logger = get_logger(__name__)
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\nScraping interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
