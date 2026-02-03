"""
Main scraper runner.
"""

import sys
import argparse
import logging
from api_scraper import get_rankings
from html_scraper import scrape_rankings_html
from exporter import export_to_csv
from logger import get_logger
from config import init_dirs

logger = get_logger(__name__)

def configure_log_level(log_level: str):
    """
    Configure logging level for application loggers only.

    Parameters:
    - log_level: Logging level string (DEBUG, INFO, WARNING, ERROR)
    """
    init_dirs()

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

def main():
    """
    Main entry point with command-line argument support.
    Tries API with pagination for both genders, falls back to HTML if needed.
    """
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
        genders = ["male", "female"]
    else:
        genders = [args.gender]

    success_count = 0
    failure_count = 0

    for gender in genders:
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"Processing {gender.capitalize()} Rankings")
        logger.info("=" * 60)

        try:
            df = get_rankings(
                gender=gender,
                page_size=args.page_size,
                max_pages=args.max_pages,
                resume=not args.no_resume,
            )

            output_file = f"psa_rankings_{gender}.csv"
            export_to_csv(df, output_file)

            logger.info(f"Successfully scraped {len(df)} {gender} players")
            logger.info(f"Data exported to: {output_file}")
            success_count += 1

        except Exception as e:
            logger.error(f"API failed for {gender}: {e}")
            logger.info(f"Attempting HTML fallback for {gender}...")

            try:
                df_fallback = scrape_rankings_html()
                fallback_file = f"psa_rankings_{gender}_fallback.csv"
                export_to_csv(df_fallback, fallback_file)
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

    sys.exit(0 if failure_count == 0 else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\nScraping interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
