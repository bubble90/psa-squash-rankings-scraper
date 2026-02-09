"""
Test suite for schema types and type guards.
"""

from schema import (
    ApiPlayerRecord,
    HtmlPlayerRecord,
    is_api_result,
    is_html_result,
)


def test_api_player_record_structure() -> None:
    """Test that ApiPlayerRecord has correct structure."""
    record: ApiPlayerRecord = {
        "rank": 1,
        "player": "Test Player",
        "id": 12345,
        "tournaments": 10,
        "points": 5000,
        "height_cm": 180,
        "weight_kg": 75,
        "birthdate": "1990-01-01",
        "country": "Egypt",
        "source": "api",
    }

    assert record["rank"] == 1
    assert record["player"] == "Test Player"
    assert record["id"] == 12345
    assert record["tournaments"] == 10
    assert record["points"] == 5000
    assert record["height_cm"] == 180
    assert record["weight_kg"] == 75
    assert record["birthdate"] == "1990-01-01"
    assert record["country"] == "Egypt"
    assert record["source"] == "api"


def test_api_player_record_with_none_optionals() -> None:
    """Test that ApiPlayerRecord allows None for optional fields."""
    record: ApiPlayerRecord = {
        "rank": 1,
        "player": "Test Player",
        "id": 12345,
        "tournaments": 10,
        "points": 5000,
        "height_cm": None,
        "weight_kg": None,
        "birthdate": None,
        "country": None,
        "source": "api",
    }

    assert record["height_cm"] is None
    assert record["weight_kg"] is None
    assert record["birthdate"] is None
    assert record["country"] is None


def test_html_player_record_structure() -> None:
    """Test that HtmlPlayerRecord has correct structure."""
    record: HtmlPlayerRecord = {
        "rank": 1,
        "player": "Test Player",
        "tournaments": 10,
        "points": 5000,
        "source": "html",
    }

    assert record["rank"] == 1
    assert record["player"] == "Test Player"
    assert record["tournaments"] == 10
    assert record["points"] == 5000
    assert record["source"] == "html"


def test_html_player_record_missing_fields() -> None:
    """Test that HtmlPlayerRecord doesn't have ID or biographical fields."""
    record: HtmlPlayerRecord = {
        "rank": 1,
        "player": "Test Player",
        "tournaments": 10,
        "points": 5000,
        "source": "html",
    }

    assert "id" not in record
    assert "height_cm" not in record
    assert "weight_kg" not in record
    assert "birthdate" not in record
    assert "country" not in record


def test_is_api_result_with_api_data() -> None:
    """Test is_api_result returns True for API data."""
    api_data: list[ApiPlayerRecord] = [
        {
            "rank": 1,
            "player": "Test",
            "id": 1,
            "tournaments": 5,
            "points": 1000,
            "height_cm": None,
            "weight_kg": None,
            "birthdate": None,
            "country": None,
            "source": "api",
        }
    ]

    assert is_api_result(api_data) is True


def test_is_api_result_with_html_data() -> None:
    """Test is_api_result returns False for HTML data."""
    html_data: list[HtmlPlayerRecord] = [
        {
            "rank": 1,
            "player": "Test",
            "tournaments": 5,
            "points": 1000,
            "source": "html",
        }
    ]

    assert is_api_result(html_data) is False


def test_is_api_result_with_empty_list() -> None:
    """Test is_api_result returns False for empty list."""
    empty_data: list[ApiPlayerRecord] = []

    assert is_api_result(empty_data) is False


def test_is_html_result_with_html_data() -> None:
    """Test is_html_result returns True for HTML data."""
    html_data: list[HtmlPlayerRecord] = [
        {
            "rank": 1,
            "player": "Test",
            "tournaments": 5,
            "points": 1000,
            "source": "html",
        }
    ]

    assert is_html_result(html_data) is True


def test_is_html_result_with_api_data() -> None:
    """Test is_html_result returns False for API data."""
    api_data: list[ApiPlayerRecord] = [
        {
            "rank": 1,
            "player": "Test",
            "id": 1,
            "tournaments": 5,
            "points": 1000,
            "height_cm": None,
            "weight_kg": None,
            "birthdate": None,
            "country": None,
            "source": "api",
        }
    ]

    assert is_html_result(api_data) is False


def test_is_html_result_with_empty_list() -> None:
    """Test is_html_result returns False for empty list."""
    empty_data: list[HtmlPlayerRecord] = []

    assert is_html_result(empty_data) is False


def test_type_guards_are_mutually_exclusive() -> None:
    """Test that a dataset cannot be both API and HTML result."""
    api_data: list[ApiPlayerRecord] = [
        {
            "rank": 1,
            "player": "Test",
            "id": 1,
            "tournaments": 5,
            "points": 1000,
            "height_cm": None,
            "weight_kg": None,
            "birthdate": None,
            "country": None,
            "source": "api",
        }
    ]

    html_data: list[HtmlPlayerRecord] = [
        {
            "rank": 1,
            "player": "Test",
            "tournaments": 5,
            "points": 1000,
            "source": "html",
        }
    ]

    assert is_api_result(api_data) is True
    assert is_html_result(api_data) is False

    assert is_html_result(html_data) is True
    assert is_api_result(html_data) is False


def test_api_record_source_literal() -> None:
    """Test that API record source must be 'api'."""
    record: ApiPlayerRecord = {
        "rank": 1,
        "player": "Test",
        "id": 1,
        "tournaments": 5,
        "points": 1000,
        "height_cm": None,
        "weight_kg": None,
        "birthdate": None,
        "country": None,
        "source": "api",
    }

    assert record["source"] == "api"


def test_html_record_source_literal() -> None:
    """Test that HTML record source must be 'html'."""
    record: HtmlPlayerRecord = {
        "rank": 1,
        "player": "Test",
        "tournaments": 5,
        "points": 1000,
        "source": "html",
    }

    assert record["source"] == "html"


def test_api_record_optional_fields_can_be_none() -> None:
    """Test that optional fields in API records can be None."""
    record: ApiPlayerRecord = {
        "rank": 1,
        "player": "Test",
        "id": 1,
        "tournaments": 5,
        "points": 1000,
        "height_cm": None,
        "weight_kg": None,
        "birthdate": None,
        "country": None,
        "source": "api",
    }

    assert record["height_cm"] is None
    assert record["weight_kg"] is None
    assert record["birthdate"] is None
    assert record["country"] is None


def test_api_record_optional_fields_can_have_values() -> None:
    """Test that optional fields in API records can have actual values."""
    record: ApiPlayerRecord = {
        "rank": 1,
        "player": "Test",
        "id": 1,
        "tournaments": 5,
        "points": 1000,
        "height_cm": 180,
        "weight_kg": 75,
        "birthdate": "1990-01-01",
        "country": "Egypt",
        "source": "api",
    }

    assert record["height_cm"] == 180
    assert record["weight_kg"] == 75
    assert record["birthdate"] == "1990-01-01"
    assert record["country"] == "Egypt"


def test_multiple_api_records() -> None:
    """Test type guard with multiple API records."""
    api_data: list[ApiPlayerRecord] = [
        {
            "rank": i,
            "player": f"Player {i}",
            "id": i,
            "tournaments": 5,
            "points": 1000,
            "height_cm": None,
            "weight_kg": None,
            "birthdate": None,
            "country": None,
            "source": "api",
        }
        for i in range(1, 6)
    ]

    assert is_api_result(api_data) is True
    assert len(api_data) == 5


def test_multiple_html_records() -> None:
    """Test type guard with multiple HTML records."""
    html_data: list[HtmlPlayerRecord] = [
        {
            "rank": i,
            "player": f"Player {i}",
            "tournaments": 5,
            "points": 1000,
            "source": "html",
        }
        for i in range(1, 6)
    ]

    assert is_html_result(html_data) is True
    assert len(html_data) == 5
