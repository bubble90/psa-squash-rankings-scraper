"""
Shared parsing utilities for PSA Squash rankings scrapers.

Includes schema validation to detect API changes early
and prevent silent data corruption.
"""

import re
from logger import get_logger


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

def parse_measure(value, unit_label):
    """
    Robustly parses a measurement string (e.g., '185cm', '185 cm', '185').
    Returns an int or raises a descriptive ValueError.
    """
    if not value or not str(value).strip():
        return "N/A"

    clean_value = re.sub(r'[^0-9]', '', str(value))

    if not clean_value:
        raise ValueError(
            f"Invalid format for {unit_label}: '{value}'. "
            f"Expected numeric value (e.g., '185cm' or '185')."
        )

    return int(clean_value)

def parse_api_player(player: dict):
    """
    Validate and extract required fields from
    a PSA API player object.

    Returns:
        dict: normalized ranking record
    """
    logger = get_logger(__name__)

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
        
    if player.get("Height"):
        try:
            parsed["height(cm)"] = parse_measure(player["Height"], "Height")
        except ValueError as e:
            logger.warning(f"Skipping height for {player.get('Name')}: {e}")
            parsed["height(cm)"] = "N/A"

    if player.get("Weight"):
        try:
            parsed["weight(kg)"] = parse_measure(player["Weight"], "Weight")
        except ValueError as e:
            logger.warning(f"Skipping weight for {player.get('Name')}: {e}")
            parsed["weight(kg)"] = "N/A"

    if "Country" in player:
        parsed["country"] = player["Country"]

    logger.debug(f"Parsed player: {parsed['player']} (Rank: {parsed['rank']})")
    return parsed
