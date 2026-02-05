import pytest
from data_parser import parse_api_player, validate_api_schema


def test_validate_api_schema_success():
    """Test that valid data passes schema validation."""
    valid_player = {
        "World Ranking": 1,
        "Name": "Ali Farag",
        "Id": 12345,
        "Tournaments": 12,
        "Total Points": 20000,
    }
    validate_api_schema(valid_player)


def test_validate_api_schema_failure():
    """Test that missing fields raise a ValueError."""
    invalid_player = {"Name": "Ali Farag", "Tournaments": 12}
    with pytest.raises(ValueError, match="Missing fields"):
        validate_api_schema(invalid_player)


def test_parse_api_player_transformation():
    """Test that the parser correctly renames and converts fields."""
    raw_data = {
        "World Ranking": "5",
        "Name": "Mohamed ElShorbagy",
        "Id": 12345,
        "Tournaments": "10",
        "Total Points": "15000",
    }
    parsed = parse_api_player(raw_data)

    assert parsed["rank"] == "5"
    assert parsed["player"] == "Mohamed ElShorbagy"
    assert isinstance(parsed["tournaments"], int)
    assert parsed["points"] == 15000
    assert parsed["birthdate"] is None
    assert parsed["height(cm)"] is None
    assert parsed["weight(kg)"] is None
    assert parsed["country"] is None


def test_parse_api_player_with_all_optional_fields():
    """Test that the parser correctly extracts all optional fields when present."""
    raw_data = {
        "World Ranking": "1",
        "Name": "Ali Farag",
        "Id": "12345",
        "Tournaments": "12",
        "Total Points": "20000",
        "Birthdate": "1992-01-01",
        "Height": "180cm",
        "Weight": "75kg",
        "Country": "Egypt",
    }
    parsed = parse_api_player(raw_data)

    assert parsed["rank"] == "1"
    assert parsed["player"] == "Ali Farag"
    assert parsed["id"] == 12345
    assert parsed["birthdate"] == "1992-01-01"
    assert parsed["height(cm)"] == 180
    assert parsed["weight(kg)"] == 75
    assert parsed["country"] == "Egypt"
