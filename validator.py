"""
Validator for PSA Squash rankings scrapers.

Compares HTML and API scraper outputs to validate completeness.
"""

import pandas as pd
from pandas.errors import EmptyDataError
from logger import get_logger
from config import OUTPUT_DIR
from typing import Literal, Dict, Any

REQUIRED_API_FIELDS = {
    "World Ranking",
    "Name",
    "Id",
    "Tournaments",
    "Total Points",
}


def validate_api_schema(player: Dict[str, Any]) -> None:
    """
    Validate that a single API player object
    contains all required fields.

    Raises:
        ValueError: if the API schema is missing fields
    """
    logger = get_logger(__name__)

    missing_fields = REQUIRED_API_FIELDS - player.keys()

    if missing_fields:
        logger.error(f"API schema validation failed. Missing fields: {missing_fields}")
        raise ValueError(
            f"API schema validation failed. Missing fields: {missing_fields}"
        )

    logger.debug(
        f"Schema validation passed for player: {player.get('Name', 'Unknown')}"
    )


def validate_scraped_data(gender: Literal["male", "female"] = "male") -> None:
    """
    Validate scraped data for a specific gender.

    Parameters:
    - gender: 'male' or 'female'
    """
    logger = get_logger(__name__)

    logger.info(f"Starting validation for {gender} rankings")

    API_FILE = OUTPUT_DIR / f"psa_rankings_{gender}.csv"
    HTML_FILE = OUTPUT_DIR / f"psa_rankings_{gender}_fallback.csv"

    api_exists = API_FILE.exists()
    html_exists = HTML_FILE.exists()

    if not api_exists and not html_exists:
        logger.error(f"No data files found for {gender}. Run the scraper first:")
        logger.error(f"  python run_scraper.py --gender {gender}")
        return

    api_df = pd.DataFrame()
    if api_exists:
        try:
            api_df = pd.read_csv(API_FILE)
            logger.info(f"Loaded API file: {len(api_df)} rows from {API_FILE}")
        except Exception as e:
            logger.error(f"Failed to load API file: {e}")
    else:
        logger.warning(f"API file not found: {API_FILE}")

    html_df = pd.DataFrame()
    if html_exists:
        try:
            html_df = pd.read_csv(HTML_FILE)
            logger.info(f"Loaded HTML file: {len(html_df)} rows from {HTML_FILE}")
        except EmptyDataError:
            logger.warning("HTML file is empty")
        except Exception as e:
            logger.error(f"Failed to load HTML file: {e}")
    else:
        logger.info(
            f"HTML fallback file not found: {HTML_FILE} (this is normal if API scraping succeeded)"
        )

    logger.info("-" * 60)
    logger.info(f"HTML scraper rows: {len(html_df)}")
    logger.info(f"API scraper rows: {len(api_df)}")

    if len(api_df) > 0:
        logger.info(f"API scraper successfully returned {len(api_df)} {gender} players")

        logger.info(f"\nTop 5 {gender} players:")
        for idx, row in api_df.head(5).iterrows():
            logger.info(f"  {row['rank']}. {row['player']} - {row['points']} points")
    else:
        logger.warning("API scraper returned no data")

    if len(html_df) == 0:
        logger.info("HTML scraper returned no data (expected if API succeeded)")

    if len(html_df) > 0 and len(api_df) > 0:
        logger.info("\nComparing HTML vs API results:")

        if html_df.iloc[0]["player"] == api_df.iloc[0]["player"]:
            logger.info("Top-ranked player matches between HTML and API")
        else:
            logger.warning("Top-ranked player does NOT match:")
            logger.warning(f"  HTML: {html_df.iloc[0]['player']}")
            logger.warning(f"  API:  {api_df.iloc[0]['player']}")

        diff = abs(len(html_df) - len(api_df))
        if diff == 0:
            logger.info("Row counts match exactly")
        else:
            logger.warning(f"Row count difference: {diff} players")

    logger.info("-" * 60)
    logger.info(f"Validation complete for {gender}")


if __name__ == "__main__":
    logger = get_logger(__name__)

    import sys

    logger.info("=" * 60)
    logger.info("PSA Rankings Data Validator")
    logger.info("=" * 60)

    gender = sys.argv[1] if len(sys.argv) > 1 else "both"

    if gender == "both":
        validate_scraped_data("male")
        print()
        validate_scraped_data("female")
    elif gender in ["male", "female"]:
        validate_scraped_data(gender) # type: ignore
    else:
        logger.error(f"Invalid gender: {gender}. Use 'male', 'female', or 'both'")
        logger.info("Usage: python validator.py [male|female|both]")

    logger.info("=" * 60)
