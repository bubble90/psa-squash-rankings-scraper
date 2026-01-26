"""
Shared parsing utilities for PSA Squash rankings scrapers.

Includes schema validation to detect API changes early
and prevent silent data corruption.
"""

from logger import get_logger

logger = get_logger(__name__)

REQUIRED_API_FIELDS = {
    "World Ranking",
    "Name",
    "Id",
    "Tournaments",
    "Total Points",
}


def validate_api_schema(player: dict):
    """
    Validate that a single API player object
    contains all required fields.

    Raises:
        ValueError: if the API schema is missing fields
    """
    missing_fields = REQUIRED_API_FIELDS - player.keys()

    if missing_fields:
        logger.error(f"API schema validation failed. Missing fields: {missing_fields}")
        raise ValueError(
            f"API schema validation failed. Missing fields: {missing_fields}"
        )

    logger.debug(
        f"Schema validation passed for player: {player.get('Name', 'Unknown')}"
    )


def parse_api_player(player: dict):
    """
    Validate and extract required fields from
    a PSA API player object.

    Returns:
        dict: normalized ranking record
    """
    validate_api_schema(player)

    parsed = {
        "rank": player["World Ranking"],
        "player": player["Name"],
        "id": int(player["Id"]),
        "tournaments": int(player["Tournaments"]),
        "points": int(player["Total Points"]),
        "height(cm)": "N/A",
        "weight(kg)": "N/A",
        "birthdate": "N/A",
        "country": "N/A",
    }

    if "Birthdate" in player:
        parsed["birthdate"] = player["Birthdate"]
    if "Height" in player:
        parsed["height(cm)"] = int(player["Height"][:-2])
    if "Weight" in player:
        parsed["weight(kg)"] = int(player["Weight"][:-2])
    if "Country" in player:
        parsed["country"] = player["Country"]

    logger.debug(f"Parsed player: {parsed['player']} (Rank: {parsed['rank']})")
    return parsed





