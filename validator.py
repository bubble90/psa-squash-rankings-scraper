"""
Validator for PSA Squash rankings scrapers.

Validates schema consistency and compares API vs HTML scraper outputs
with explicit handling of their different data structures.
"""

import pandas as pd
from pandas.errors import EmptyDataError
from logger import get_logger
from config import OUTPUT_DIR
from typing import Literal, Any


REQUIRED_API_FIELDS = {
    "World Ranking",
    "Name",
    "Id",
    "Tournaments",
    "Total Points",
}


def validate_api_schema(player: dict[str, Any]) -> None:
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
    Validate scraped data for a specific gender with type-aware comparison.

    This function understands that API and HTML scrapers produce different schemas
    and validates accordingly.

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
    api_source = None

    if api_exists:
        try:
            api_df = pd.read_csv(API_FILE)
            if 'source' in api_df.columns and len(api_df) > 0:
                api_source = api_df['source'].iloc[0]
            logger.info(f"Loaded API file: {len(api_df)} rows from {API_FILE}")
            if api_source:
                logger.info(f"  Data source: {api_source}")
        except Exception as e:
            logger.error(f"Failed to load API file: {e}")
    else:
        logger.warning(f"API file not found: {API_FILE}")

    html_df = pd.DataFrame()
    html_source = None

    if html_exists:
        try:
            html_df = pd.read_csv(HTML_FILE)
            if 'source' in html_df.columns and len(html_df) > 0:
                html_source = html_df['source'].iloc[0]
            logger.info(f"Loaded HTML file: {len(html_df)} rows from {HTML_FILE}")
            if html_source:
                logger.info(f"  Data source: {html_source}")
        except EmptyDataError:
            logger.warning("HTML file is empty")
        except Exception as e:
            logger.error(f"Failed to load HTML file: {e}")
    else:
        logger.info(
            f"HTML fallback file not found: {HTML_FILE} (this is normal if API scraping succeeded)"
        )

    logger.info("-" * 60)
    logger.info("Data Quality Assessment:")
    logger.info("-" * 60)

    if len(api_df) > 0:
        logger.info(f"\nAPI scraper results ({len(api_df)} players):")

        if api_source == "api":
            logger.info("  ✓ Data source: API (COMPLETE DATA)")
            logger.info("  ✓ Contains player IDs: Yes")
            logger.info("  ✓ Contains biographical data: Yes")

            expected_cols = {'rank', 'player', 'id', 'tournaments', 'points',
                           'height_cm', 'weight_kg', 'birthdate', 'country', 'source'}
            missing_cols = expected_cols - set(api_df.columns)
            if missing_cols:
                logger.warning(f"  ⚠ Missing expected columns: {missing_cols}")
            else:
                logger.info("  ✓ Schema complete")

        elif api_source == "html":
            logger.warning("  ⚠ Data source: HTML fallback (DEGRADED DATA)")
            logger.warning("  ✗ Contains player IDs: No")
            logger.warning("  ✗ Contains biographical data: No")
            logger.warning("  ⚠ This data cannot be used for:")
            logger.warning("    - Joining with other datasets (no unique ID)")
            logger.warning("    - Player tracking across time (no unique ID)")
            logger.warning("    - Biographical analysis (missing height, weight, etc.)")

        logger.info(f"\n  Top 5 {gender} players:")
        for idx, row in api_df.head(5).iterrows():
            player_id = f" (ID: {row['id']})" if 'id' in row and pd.notna(row['id']) and row['id'] != -1 else " (no ID)"
            logger.info(f"    {row['rank']}. {row['player']}{player_id} - {row['points']} points")

    if len(html_df) > 0:
        logger.info(f"\nHTML scraper results ({len(html_df)} players):")
        logger.warning("  ⚠ Data source: HTML fallback (DEGRADED DATA)")
        logger.warning("  ✗ This is limited data for fallback purposes only")

        expected_html_cols = {'rank', 'player', 'tournaments', 'points', 'source'}
        missing_cols = expected_html_cols - set(html_df.columns)
        extra_cols = set(html_df.columns) - expected_html_cols

        if missing_cols:
            logger.error(f"  ✗ Missing expected columns: {missing_cols}")
        if extra_cols:
            logger.info(f"  ℹ Extra columns: {extra_cols}")

    if len(html_df) > 0 and len(api_df) > 0:
        logger.info("\n" + "=" * 60)
        logger.info("Comparing API vs HTML results:")
        logger.info("=" * 60)

        if api_df.iloc[0]["player"] == html_df.iloc[0]["player"]:
            logger.info("✓ Top-ranked player matches between sources")
        else:
            logger.warning("✗ Top-ranked player does NOT match:")
            logger.warning(f"    API:  {api_df.iloc[0]['player']}")
            logger.warning(f"    HTML: {html_df.iloc[0]['player']}")

        diff = abs(len(html_df) - len(api_df))
        if diff == 0:
            logger.info("✓ Row counts match exactly")
        else:
            logger.warning(f"⚠ Row count difference: {diff} players")
            logger.info(f"    API:  {len(api_df)} players")
            logger.info(f"    HTML: {len(html_df)} players")

    # Summary and recommendations
    logger.info("\n" + "=" * 60)
    logger.info("Validation Summary:")
    logger.info("=" * 60)

    if len(api_df) > 0 and api_source == "api":
        logger.info("✓ COMPLETE API DATA AVAILABLE - recommended for production use")
    elif len(api_df) > 0 and api_source == "html":
        logger.warning("⚠ DEGRADED HTML DATA - suitable only for display purposes")
        logger.warning("⚠ Re-run scraper to obtain complete API data if possible")
    elif len(html_df) > 0:
        logger.warning("⚠ ONLY HTML FALLBACK DATA AVAILABLE")
        logger.warning("⚠ This is degraded data without player IDs or biographical info")
    else:
        logger.error("✗ NO VALID DATA FOUND")

    logger.info("-" * 60)


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
        validate_scraped_data(gender)  # type: ignore
    else:
        logger.error(f"Invalid gender: {gender}. Use 'male', 'female', or 'both'")
        logger.info("Usage: python validator.py [male|female|both]")

    logger.info("=" * 60)
