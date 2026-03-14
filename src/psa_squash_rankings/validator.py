"""
Validator for PSA Squash rankings scrapers.

Validates schema consistency and compares API vs HTML scraper outputs
with explicit handling of their different data structures.
"""

import pandas as pd
from pandas.errors import EmptyDataError
from psa_squash_rankings.logger import get_logger
from psa_squash_rankings.config import OUTPUT_DIR
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
            if "source" in api_df.columns and len(api_df) > 0:
                api_source = api_df["source"].iloc[0]
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
            if "source" in html_df.columns and len(html_df) > 0:
                html_source = html_df["source"].iloc[0]
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

            expected_cols = {
                "rank",
                "player",
                "id",
                "tournaments",
                "points",
                "height_cm",
                "weight_kg",
                "birthdate",
                "country",
                "picture_url",
                "mugshot_url",
                "source",
            }
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
            player_id = (
                f" (ID: {row['id']})"
                if "id" in row and pd.notna(row["id"]) and row["id"] != -1
                else " (no ID)"
            )
            logger.info(
                f"    {row['rank']}. {row['player']}{player_id} - {row['points']} points"
            )

    if len(html_df) > 0:
        logger.info(f"\nHTML scraper results ({len(html_df)} players):")
        logger.warning("  ⚠ Data source: HTML fallback (DEGRADED DATA)")
        logger.warning("  ✗ This is limited data for fallback purposes only")

        expected_html_cols = {"rank", "player", "tournaments", "points", "source"}
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
        logger.warning(
            "⚠ This is degraded data without player IDs or biographical info"
        )
    else:
        logger.error("✗ NO VALID DATA FOUND")

    logger.info("-" * 60)


def validate_tournaments() -> None:
    """
    Validate the squashinfo tournaments CSV.

    Checks that required columns are present, key fields are non-null,
    and prints a summary of tiers and gender breakdown.
    """
    logger = get_logger(__name__)

    path = OUTPUT_DIR / "squashinfo_tournaments.csv"
    if not path.exists():
        logger.error(f"No tournaments file found: {path}")
        logger.error("Run:  psa-scrape tournaments")
        return

    try:
        df = pd.read_csv(path)
    except Exception as e:
        logger.error(f"Failed to load tournaments file: {e}")
        return

    logger.info(f"Loaded {len(df)} tournaments from {path}")

    required_cols = {"id", "name", "tier", "location", "date", "url", "source"}
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        logger.error(f"  ✗ Missing columns: {missing_cols}")
    else:
        logger.info("  ✓ All required columns present")

    for col in ("id", "name", "tier", "date", "url"):
        if col in df.columns:
            null_count = df[col].isna().sum()
            if null_count:
                logger.warning(f"  ⚠ '{col}' has {null_count} null value(s)")

    if "tier" in df.columns:
        logger.info("\n  Tier breakdown:")
        for tier, count in df["tier"].value_counts().items():
            logger.info(f"    {tier}: {count}")

    if "gender" in df.columns:
        logger.info("\n  Gender breakdown:")
        for gender, count in df["gender"].value_counts(dropna=False).items():
            label = gender if pd.notna(gender) else "unknown"
            logger.info(f"    {label}: {count}")

    if "source" in df.columns:
        sources = df["source"].unique().tolist()
        logger.info(f"\n  Sources: {sources}")

    logger.info("\n  ✓ Tournament validation complete")


def validate_matches(event_id: int) -> None:
    """
    Validate the squashinfo matches CSV for a given event ID.

    Checks required columns, null rates on key fields, and prints
    a summary of rounds and completed vs upcoming matches.

    Parameters:
    - event_id: numeric tournament event ID
    """
    logger = get_logger(__name__)

    path = OUTPUT_DIR / f"squashinfo_matches_{event_id}.csv"
    if not path.exists():
        logger.error(f"No matches file found: {path}")
        logger.error(f"Run:  psa-scrape matches --event-id {event_id} --slug <slug>")
        return

    try:
        df = pd.read_csv(path)
    except Exception as e:
        logger.error(f"Failed to load matches file: {e}")
        return

    logger.info(f"Loaded {len(df)} matches from {path}")

    required_cols = {
        "match_id",
        "tournament_id",
        "tournament_name",
        "round",
        "player1_name",
        "player2_name",
        "winner",
        "scores",
        "source",
    }
    missing_cols = required_cols - set(df.columns)
    if missing_cols:
        logger.error(f"  ✗ Missing columns: {missing_cols}")
    else:
        logger.info("  ✓ All required columns present")

    for col in ("match_id", "player1_name", "player2_name", "round"):
        if col in df.columns:
            null_count = df[col].isna().sum()
            if null_count:
                logger.warning(f"  ⚠ '{col}' has {null_count} null value(s)")

    if "winner" in df.columns:
        completed = df["winner"].notna().sum()
        upcoming = df["winner"].isna().sum()
        logger.info(f"\n  Completed matches: {completed}")
        logger.info(f"  Upcoming matches:  {upcoming}")

    if "round" in df.columns:
        logger.info("\n  Round breakdown:")
        for round_name, count in df["round"].value_counts().items():
            logger.info(f"    {round_name}: {count} match(es)")

    if "duration_minutes" in df.columns:
        completed_df = df[df["duration_minutes"].notna()]
        if len(completed_df) > 0:
            avg = completed_df["duration_minutes"].mean()
            logger.info(f"\n  Avg match duration: {avg:.0f} min")

    logger.info("\n  ✓ Match validation complete")


if __name__ == "__main__":
    logger = get_logger(__name__)

    import sys

    logger.info("=" * 60)
    logger.info("PSA Squash Data Validator")
    logger.info("=" * 60)

    command = sys.argv[1] if len(sys.argv) > 1 else "both"

    if command in ("male", "female", "both"):
        genders = ["male", "female"] if command == "both" else [command]
        for g in genders:
            validate_scraped_data(g)  # type: ignore
            print()
    elif command == "tournaments":
        validate_tournaments()
    elif command == "matches":
        if len(sys.argv) < 3:
            logger.error("Usage: python -m psa_squash_rankings.validator matches <event_id>")
        else:
            validate_matches(int(sys.argv[2]))
    else:
        logger.error(f"Unknown command: {command}")
        logger.info("Usage: python -m psa_squash_rankings.validator [male|female|both|tournaments|matches <event_id>]")

    logger.info("=" * 60)
