"""
Test suite for data parser functionality.
"""

import pytest
from data_parser import parse_api_player
from validator import validate_api_schema


def test_validate_api_schema_success() -> None:
    """Test that valid data passes schema validation."""
    valid_player = {
        "World Ranking": 1,
        "Name": "Ali Farag",
        "Id": 12345,
        "Tournaments": 12,
        "Total Points": 20000,
    }
    validate_api_schema(valid_player)


def test_validate_api_schema_failure() -> None:
    """Test that missing fields raise a ValueError."""
    invalid_player = {"Name": "Ali Farag", "Tournaments": 12}
    with pytest.raises(ValueError, match="Missing fields"):
        validate_api_schema(invalid_player)


def test_parse_api_player_transformation() -> None:
    """Test that the parser correctly renames and converts fields."""
    raw_data = {
        "World Ranking": 5,
        "Name": "Mohamed ElShorbagy",
        "Id": 12345,
        "Tournaments": 10,
        "Total Points": 15000,
    }
    parsed = parse_api_player(raw_data)

    assert parsed["rank"] == 5
    assert parsed["player"] == "Mohamed ElShorbagy"
    assert isinstance(parsed["tournaments"], int)
    assert parsed["tournaments"] == 10
    assert parsed["points"] == 15000
    assert parsed["id"] == 12345
    assert parsed["birthdate"] is None
    assert parsed["height_cm"] is None
    assert parsed["weight_kg"] is None
    assert parsed["country"] is None
    assert parsed["source"] == "api"


def test_parse_api_player_with_all_optional_fields() -> None:
    """Test that the parser correctly extracts all optional fields when present."""
    raw_data = {
        "World Ranking": 1,
        "Name": "Ali Farag",
        "Id": 12345,
        "Tournaments": 12,
        "Total Points": 20000,
        "Birthdate": "1992-01-01",
        "Height": "180cm",
        "Weight": "75kg",
        "Country": "Egypt",
    }
    parsed = parse_api_player(raw_data)

    assert parsed["rank"] == 1
    assert parsed["player"] == "Ali Farag"
    assert parsed["id"] == 12345
    assert parsed["tournaments"] == 12
    assert parsed["points"] == 20000
    assert parsed["birthdate"] == "1992-01-01"
    assert parsed["height_cm"] == 180
    assert parsed["weight_kg"] == 75
    assert parsed["country"] == "Egypt"
    assert parsed["source"] == "api"


def test_parse_api_player_height_conversion() -> None:
    """Test height conversion from various formats."""
    raw_data_cm = {
        "World Ranking": 1,
        "Name": "Player",
        "Id": 1,
        "Tournaments": 1,
        "Total Points": 1000,
        "Height": "185cm",
    }
    parsed = parse_api_player(raw_data_cm)
    assert parsed["height_cm"] == 185

    raw_data_cm_space = {
        "World Ranking": 1,
        "Name": "Player",
        "Id": 1,
        "Tournaments": 1,
        "Total Points": 1000,
        "Height": "185 cm",
    }
    parsed = parse_api_player(raw_data_cm_space)
    assert parsed["height_cm"] == 185


def test_parse_api_player_weight_conversion() -> None:
    """Test weight conversion from various formats."""
    raw_data_kg = {
        "World Ranking": 1,
        "Name": "Player",
        "Id": 1,
        "Tournaments": 1,
        "Total Points": 1000,
        "Weight": "75kg",
    }
    parsed = parse_api_player(raw_data_kg)
    assert parsed["weight_kg"] == 75

    raw_data_kg_space = {
        "World Ranking": 1,
        "Name": "Player",
        "Id": 1,
        "Tournaments": 1,
        "Total Points": 1000,
        "Weight": "75 kg",
    }
    parsed = parse_api_player(raw_data_kg_space)
    assert parsed["weight_kg"] == 75


def test_parse_api_player_missing_optional_fields() -> None:
    """Test parser handles missing optional fields gracefully."""
    raw_data = {
        "World Ranking": 1,
        "Name": "Player",
        "Id": 1,
        "Tournaments": 1,
        "Total Points": 1000,
    }
    parsed = parse_api_player(raw_data)

    assert parsed["birthdate"] is None
    assert parsed["height_cm"] is None
    assert parsed["weight_kg"] is None
    assert parsed["country"] is None
    assert parsed["source"] == "api"
