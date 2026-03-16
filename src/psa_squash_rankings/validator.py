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


REQUIRED_PLAYER_MATCH_FIELDS = {
    "player_id",
    "tournament_name",
    "round",
    "opponent_name",
    "result",
    "source",
}

REQUIRED_PLAYER_TOURNAMENT_FIELDS = {
    "player_id",
    "tournament_name",
    "round_reached",
    "source",
}


def validate_player_match_record(match: dict[str, Any]) -> None:
    """
    Validate a single PlayerRecentMatchRecord.

    Raises:
        ValueError: if required fields are missing or values are invalid.
    """
    logger = get_logger(__name__)

    missing = REQUIRED_PLAYER_MATCH_FIELDS - match.keys()
    if missing:
        raise ValueError(f"PlayerRecentMatchRecord missing fields: {missing}")

    if match.get("source") != "squashinfo":
        raise ValueError(
            f"PlayerRecentMatchRecord source must be 'squashinfo', got {match.get('source')!r}"
        )

    result = match.get("result")
    if result not in ("W", "L", ""):
        raise ValueError(
            f"PlayerRecentMatchRecord result must be 'W', 'L', or '', got {result!r}"
        )

    if not isinstance(match.get("player_id"), int) or match["player_id"] <= 0:
        raise ValueError(
            f"PlayerRecentMatchRecord player_id must be a positive int, got {match.get('player_id')!r}"
        )

    logger.debug(
        f"Match record validation passed: player {match['player_id']} vs {match.get('opponent_name')}"
    )


def validate_player_tournament_record(tournament: dict[str, Any]) -> None:
    """
    Validate a single PlayerRecentTournamentRecord.

    Raises:
        ValueError: if required fields are missing or values are invalid.
    """
    logger = get_logger(__name__)

    missing = REQUIRED_PLAYER_TOURNAMENT_FIELDS - tournament.keys()
    if missing:
        raise ValueError(f"PlayerRecentTournamentRecord missing fields: {missing}")

    if tournament.get("source") != "squashinfo":
        raise ValueError(
            f"PlayerRecentTournamentRecord source must be 'squashinfo', got {tournament.get('source')!r}"
        )

    if not isinstance(tournament.get("player_id"), int) or tournament["player_id"] <= 0:
        raise ValueError(
            f"PlayerRecentTournamentRecord player_id must be a positive int, got {tournament.get('player_id')!r}"
        )

    logger.debug(
        f"Tournament record validation passed: player {tournament['player_id']} at {tournament.get('tournament_name')}"
    )


def validate_player_data(player_id: int) -> None:
    """
    Validate scraped player history CSVs for a given player ID.

    Loads squashinfo_player_{player_id}_matches.csv and
    squashinfo_player_{player_id}_tournaments.csv from OUTPUT_DIR,
    checks column completeness, and reports data quality stats.

    Parameters:
    - player_id: numeric player ID (e.g. 5974)
    """
    logger = get_logger(__name__)
    logger.info(f"Starting validation for player {player_id}")

    matches_file = OUTPUT_DIR / f"squashinfo_player_{player_id}_matches.csv"
    tournaments_file = OUTPUT_DIR / f"squashinfo_player_{player_id}_tournaments.csv"

    expected_match_cols = {
        "player_id",
        "tournament_id",
        "tournament_name",
        "round",
        "opponent_name",
        "opponent_id",
        "opponent_country",
        "result",
        "scores",
        "duration_minutes",
        "date",
        "source",
    }
    expected_tournament_cols = {
        "player_id",
        "tournament_id",
        "tournament_name",
        "tier",
        "location",
        "date",
        "round_reached",
        "source",
    }

    logger.info("-" * 60)
    logger.info("Matches:")
    logger.info("-" * 60)

    if not matches_file.exists():
        logger.warning(f"Matches file not found: {matches_file}")
    else:
        try:
            df = pd.read_csv(matches_file)
            logger.info(f"Loaded {len(df)} matches from {matches_file}")

            missing_cols = expected_match_cols - set(df.columns)
            if missing_cols:
                logger.warning(f"Missing expected columns: {missing_cols}")
            else:
                logger.info("Schema complete")

            if len(df) > 0:
                wins = (df["result"] == "W").sum()
                losses = (df["result"] == "L").sum()
                upcoming = (df["result"] == "").sum()
                logger.info(f"Results: {wins}W / {losses}L / {upcoming} upcoming")

                invalid_results = df[~df["result"].isin(["W", "L", ""])][
                    "result"
                ].unique()
                if len(invalid_results):
                    logger.error(f"Invalid result values: {invalid_results}")

                missing_opponent = df["opponent_name"].isna().sum()
                if missing_opponent:
                    logger.warning(f"{missing_opponent} rows missing opponent_name")

        except Exception as e:
            logger.error(f"Failed to load matches file: {e}")

    logger.info("-" * 60)
    logger.info("Tournaments:")
    logger.info("-" * 60)

    if not tournaments_file.exists():
        logger.warning(f"Tournaments file not found: {tournaments_file}")
    else:
        try:
            df = pd.read_csv(tournaments_file)
            logger.info(f"Loaded {len(df)} tournaments from {tournaments_file}")

            missing_cols = expected_tournament_cols - set(df.columns)
            if missing_cols:
                logger.warning(f"Missing expected columns: {missing_cols}")
            else:
                logger.info("Schema complete")

            if len(df) > 0:
                logger.info(
                    f"Most recent: {df.iloc[0]['tournament_name']} — {df.iloc[0]['round_reached']}"
                )

                missing_round = df["round_reached"].isna().sum()
                if missing_round:
                    logger.warning(f"{missing_round} rows missing round_reached")

        except Exception as e:
            logger.error(f"Failed to load tournaments file: {e}")

    logger.info("-" * 60)


REQUIRED_PSA_PLAYER_BIO_FIELDS = {
    "player_id",
    "name",
    "source",
}

PSA_PLAYER_BIO_EXPECTED_COLS = {
    "player_id",
    "name",
    "country",
    "flag_url",
    "birthdate",
    "birthplace",
    "height_cm",
    "weight_kg",
    "coach",
    "residence",
    "bio",
    "picture_url",
    "mugshot_url",
    "twitter",
    "facebook",
    "source",
}


def validate_psa_player_bio_record(record: dict[str, Any]) -> None:
    """
    Validate a single PsaPlayerBioRecord.

    Raises:
        ValueError: if required fields are missing or values are invalid.
    """
    logger = get_logger(__name__)

    missing = REQUIRED_PSA_PLAYER_BIO_FIELDS - record.keys()
    if missing:
        raise ValueError(f"PsaPlayerBioRecord missing fields: {missing}")

    if record.get("source") != "api":
        raise ValueError(
            f"PsaPlayerBioRecord source must be 'api', got {record.get('source')!r}"
        )

    if not isinstance(record.get("player_id"), int) or record["player_id"] <= 0:
        raise ValueError(
            f"PsaPlayerBioRecord player_id must be a positive int, got {record.get('player_id')!r}"
        )

    if not record.get("name"):
        raise ValueError("PsaPlayerBioRecord name must be a non-empty string")

    logger.debug(
        f"PSA bio record validation passed: player {record['player_id']} ({record.get('name')})"
    )


def validate_psa_player_bio(player_id: int) -> None:
    """
    Validate the scraped PSA biography CSV for a given player ID.

    Loads psa_player_{player_id}_bio.csv from OUTPUT_DIR and checks
    column completeness and field validity.

    Parameters:
    - player_id: numeric player ID (e.g. 11942)
    """
    logger = get_logger(__name__)
    logger.info(f"Starting PSA biography validation for player {player_id}")

    bio_file = OUTPUT_DIR / f"psa_player_{player_id}_bio.csv"

    try:
        df = pd.read_csv(bio_file)
    except FileNotFoundError:
        logger.warning(f"Biography file not found: {bio_file}")
        return
    except Exception as e:
        logger.error(f"Failed to load PSA biography file: {e}")
        logger.info("-" * 60)
        return

    logger.info(f"Loaded {len(df)} row(s) from {bio_file}")

    missing_cols = PSA_PLAYER_BIO_EXPECTED_COLS - set(df.columns)
    if missing_cols:
        logger.warning(f"Missing expected columns: {missing_cols}")
    else:
        logger.info("Schema complete")

    if len(df) > 0:
        row = df.iloc[0]
        logger.info(f"Player: {row.get('name', '')} ({row.get('country', '')})")
        if pd.notna(row.get("bio")):
            logger.info(f"Bio preview: {str(row['bio'])[:100]}...")

    logger.info("-" * 60)


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
            logger.error(
                "Usage: python -m psa_squash_rankings.validator matches <event_id>"
            )
        else:
            validate_matches(int(sys.argv[2]))
    else:
        logger.error(f"Unknown command: {command}")
        logger.info(
            "Usage: python -m psa_squash_rankings.validator [male|female|both|tournaments|matches <event_id>]"
        )

    logger.info("=" * 60)
