"""
Shared parsing utilities for PSA Squash rankings scrapers.

Includes schema validation to detect API changes early
and prevent silent data corruption.
"""

import re
from psa_squash_rankings.logger import get_logger
from typing import Any, Optional
from psa_squash_rankings.validator import validate_api_schema
from psa_squash_rankings.schema import ApiPlayerRecord


def parse_measure(value: Any, unit_label: str) -> Optional[int]:
    """
    Parses height/weight from various formats into an integer (Metric).
    Handles: "185cm", "185 cm", "185", "6' 1\"", "72in".
    Returns None if value is empty or invalid.
    """
    if not value or not str(value).strip():
        return None

    val_str = str(value).strip().lower()

    if "'" in val_str or "ft" in val_str:
        try:
            parts = re.findall(r"(\d+)", val_str)
            if len(parts) >= 2:
                feet, inches = int(parts[0]), int(parts[1])
                return round((feet * 12 + inches) * 2.54)
            elif len(parts) == 1:
                return round(int(parts[0]) * 30.48)
        except (ValueError, IndexError):
            raise ValueError(f"Malformed Imperial height in {unit_label}: '{val_str}'")

    if "in" in val_str:
        clean_inches = re.sub(r"[^0-9]", "", val_str)
        if clean_inches:
            return round(int(clean_inches) * 2.54)

    if "lb" in val_str or "pound" in val_str:
        clean_lbs = re.sub(r"[^0-9]", "", val_str)
        if clean_lbs:
            return round(int(clean_lbs) * 0.453592)

    clean_value = re.sub(r"[^0-9]", "", val_str)

    if not clean_value:
        raise ValueError(f"No numeric data found for {unit_label}: '{val_str}'")

    return int(clean_value)


def parse_api_player(player: dict[str, Any]) -> ApiPlayerRecord:
    """
    Validate and extract required fields from a PSA API player object.

    Returns:
        ApiPlayerRecord: Complete player record with all available fields

    Raises:
        ValueError: If API schema validation fails
    """
    logger = get_logger(__name__)

    validate_api_schema(player)

    parsed: ApiPlayerRecord = {
        "rank": player["World Ranking"],
        "player": player["Name"],
        "id": int(player["Id"]),
        "tournaments": int(player["Tournaments"]),
        "points": int(player["Total Points"]),
        "height_cm": None,
        "weight_kg": None,
        "birthdate": None,
        "country": None,
        "source": "api",
    }

    if "Birthdate" in player:
        parsed["birthdate"] = player["Birthdate"]

    if player.get("Height"):
        try:
            parsed["height_cm"] = parse_measure(player["Height"], "Height")
        except ValueError as e:
            logger.warning(f"Skipping height for {player.get('Name')}: {e}")
            parsed["height_cm"] = None

    if player.get("Weight"):
        try:
            parsed["weight_kg"] = parse_measure(player["Weight"], "Weight")
        except ValueError as e:
            logger.warning(f"Skipping weight for {player.get('Name')}: {e}")
            parsed["weight_kg"] = None

    if "Country" in player:
        parsed["country"] = player["Country"]

    logger.debug(f"Parsed player: {parsed['player']} (Rank: {parsed['rank']})")
    return parsed
