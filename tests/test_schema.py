"""
Test suite for schema types and type guards.
"""

from psa_squash_rankings.schema import (
    ApiPlayerRecord,
    HtmlPlayerRecord,
    TournamentRecord,
    MatchRecord,
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
        "picture_url": "https://example.com/players/12345.jpg",
        "mugshot_url": "https://example.com/mugshots/12345.jpg",
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
    assert record["picture_url"] == "https://example.com/players/12345.jpg"
    assert record["mugshot_url"] == "https://example.com/mugshots/12345.jpg"
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
        "picture_url": None,
        "mugshot_url": None,
        "source": "api",
    }

    assert record["height_cm"] is None
    assert record["weight_kg"] is None
    assert record["birthdate"] is None
    assert record["country"] is None
    assert record["picture_url"] is None
    assert record["mugshot_url"] is None


def test_html_player_record_structure() -> None:
    """Test that HtmlPlayerRecord has correct structure."""
    record: HtmlPlayerRecord = {
        "rank": 1,
        "player": "Test Player",
        "tournaments": 10,
        "points": 5000,
        "mugshot_url": "https://example.com/mugshots/player.jpg",
        "source": "html",
    }

    assert record["rank"] == 1
    assert record["player"] == "Test Player"
    assert record["tournaments"] == 10
    assert record["points"] == 5000
    assert record["mugshot_url"] == "https://example.com/mugshots/player.jpg"
    assert record["source"] == "html"


def test_html_player_record_missing_fields() -> None:
    """Test that HtmlPlayerRecord doesn't have ID or biographical fields."""
    record: HtmlPlayerRecord = {
        "rank": 1,
        "player": "Test Player",
        "tournaments": 10,
        "points": 5000,
        "mugshot_url": None,
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
            "picture_url": None,
            "mugshot_url": None,
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
            "mugshot_url": None,
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
            "mugshot_url": None,
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
            "picture_url": None,
            "mugshot_url": None,
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
            "picture_url": None,
            "mugshot_url": None,
            "source": "api",
        }
    ]

    html_data: list[HtmlPlayerRecord] = [
        {
            "rank": 1,
            "player": "Test",
            "tournaments": 5,
            "points": 1000,
            "mugshot_url": None,
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
        "picture_url": None,
        "mugshot_url": None,
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
        "mugshot_url": None,
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
        "picture_url": None,
        "mugshot_url": None,
        "source": "api",
    }

    assert record["height_cm"] is None
    assert record["weight_kg"] is None
    assert record["birthdate"] is None
    assert record["country"] is None
    assert record["picture_url"] is None
    assert record["mugshot_url"] is None


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
        "picture_url": "https://example.com/players/1.jpg",
        "mugshot_url": "https://example.com/mugshots/1.jpg",
        "source": "api",
    }

    assert record["height_cm"] == 180
    assert record["weight_kg"] == 75
    assert record["birthdate"] == "1990-01-01"
    assert record["country"] == "Egypt"
    assert record["picture_url"] == "https://example.com/players/1.jpg"
    assert record["mugshot_url"] == "https://example.com/mugshots/1.jpg"


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
            "picture_url": None,
            "mugshot_url": None,
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
            "mugshot_url": None,
            "source": "html",
        }
        for i in range(1, 6)
    ]

    assert is_html_result(html_data) is True
    assert len(html_data) == 5


# ---------------------------------------------------------------------------
# TournamentRecord
# ---------------------------------------------------------------------------


def test_tournament_record_structure() -> None:
    """Test that TournamentRecord has correct structure."""
    record: TournamentRecord = {
        "id": 11593,
        "name": "Mens Australian Open 2026",
        "gender": "M",
        "tier": "PSA Platinum",
        "location": "Sydney, Australia",
        "date": "Jan 2026",
        "url": "https://squashinfo.com/events/11593-mens-australian-open-2026",
        "source": "squashinfo",
    }

    assert record["id"] == 11593
    assert record["name"] == "Mens Australian Open 2026"
    assert record["gender"] == "M"
    assert record["tier"] == "PSA Platinum"
    assert record["location"] == "Sydney, Australia"
    assert record["date"] == "Jan 2026"
    assert (
        record["url"] == "https://squashinfo.com/events/11593-mens-australian-open-2026"
    )
    assert record["source"] == "squashinfo"


def test_tournament_record_gender_none() -> None:
    """Test that TournamentRecord allows None for gender."""
    record: TournamentRecord = {
        "id": 999,
        "name": "Some Open",
        "gender": None,
        "tier": "PSA Gold",
        "location": "Cairo, Egypt",
        "date": "Feb 2026",
        "url": "https://squashinfo.com/events/999-some-open",
        "source": "squashinfo",
    }

    assert record["gender"] is None


def test_tournament_record_gender_values() -> None:
    """Test that TournamentRecord gender accepts M and W."""
    male: TournamentRecord = {
        "id": 1,
        "name": "Mens Event",
        "gender": "M",
        "tier": "PSA Gold",
        "location": "London",
        "date": "Mar 2026",
        "url": "https://squashinfo.com/events/1-mens-event",
        "source": "squashinfo",
    }
    female: TournamentRecord = {
        "id": 2,
        "name": "Womens Event",
        "gender": "W",
        "tier": "PSA Gold",
        "location": "London",
        "date": "Mar 2026",
        "url": "https://squashinfo.com/events/2-womens-event",
        "source": "squashinfo",
    }

    assert male["gender"] == "M"
    assert female["gender"] == "W"


def test_tournament_record_source_literal() -> None:
    """Test that TournamentRecord source is 'squashinfo'."""
    record: TournamentRecord = {
        "id": 1,
        "name": "Test Event",
        "gender": None,
        "tier": "PSA Silver",
        "location": "Paris",
        "date": "Apr 2026",
        "url": "https://squashinfo.com/events/1-test-event",
        "source": "squashinfo",
    }

    assert record["source"] == "squashinfo"


def test_match_record_completed() -> None:
    """Test MatchRecord with a completed match."""
    record: MatchRecord = {
        "match_id": 98765,
        "tournament_id": 11593,
        "tournament_name": "Mens Australian Open 2026",
        "round": "Final",
        "player1_name": "Ali Farag",
        "player1_id": 42,
        "player1_country": "EGY",
        "player1_seeding": "1",
        "player2_name": "Paul Coll",
        "player2_id": 57,
        "player2_country": "NZL",
        "player2_seeding": "2",
        "winner": "Ali Farag",
        "scores": "11-5, 11-4, 11-5",
        "duration_minutes": 42,
        "source": "squashinfo",
    }

    assert record["match_id"] == 98765
    assert record["tournament_id"] == 11593
    assert record["round"] == "Final"
    assert record["player1_name"] == "Ali Farag"
    assert record["player1_id"] == 42
    assert record["player1_country"] == "EGY"
    assert record["player1_seeding"] == "1"
    assert record["player2_name"] == "Paul Coll"
    assert record["player2_id"] == 57
    assert record["player2_country"] == "NZL"
    assert record["player2_seeding"] == "2"
    assert record["winner"] == "Ali Farag"
    assert record["scores"] == "11-5, 11-4, 11-5"
    assert record["duration_minutes"] == 42
    assert record["source"] == "squashinfo"


def test_match_record_upcoming() -> None:
    """Test MatchRecord for a match not yet played."""
    record: MatchRecord = {
        "match_id": 11111,
        "tournament_id": 11593,
        "tournament_name": "Mens Australian Open 2026",
        "round": "Semi-finals",
        "player1_name": "Ali Farag",
        "player1_id": 42,
        "player1_country": "EGY",
        "player1_seeding": "1",
        "player2_name": "Paul Coll",
        "player2_id": 57,
        "player2_country": "NZL",
        "player2_seeding": "2",
        "winner": None,
        "scores": None,
        "duration_minutes": None,
        "source": "squashinfo",
    }

    assert record["winner"] is None
    assert record["scores"] is None
    assert record["duration_minutes"] is None


def test_match_record_optional_player_fields() -> None:
    """Test MatchRecord allows None for optional player fields."""
    record: MatchRecord = {
        "match_id": 22222,
        "tournament_id": 11593,
        "tournament_name": "Mens Australian Open 2026",
        "round": "Quarter-finals",
        "player1_name": "Unknown Player",
        "player1_id": None,
        "player1_country": None,
        "player1_seeding": None,
        "player2_name": "Another Player",
        "player2_id": None,
        "player2_country": None,
        "player2_seeding": None,
        "winner": None,
        "scores": None,
        "duration_minutes": None,
        "source": "squashinfo",
    }

    assert record["player1_id"] is None
    assert record["player1_country"] is None
    assert record["player1_seeding"] is None
    assert record["player2_id"] is None
    assert record["player2_country"] is None
    assert record["player2_seeding"] is None


def test_match_record_source_literal() -> None:
    """Test that MatchRecord source is 'squashinfo'."""
    record: MatchRecord = {
        "match_id": 1,
        "tournament_id": 1,
        "tournament_name": "Test Tournament",
        "round": "Final",
        "player1_name": "Player A",
        "player1_id": None,
        "player1_country": None,
        "player1_seeding": None,
        "player2_name": "Player B",
        "player2_id": None,
        "player2_country": None,
        "player2_seeding": None,
        "winner": None,
        "scores": None,
        "duration_minutes": None,
        "source": "squashinfo",
    }

    assert record["source"] == "squashinfo"


def test_match_record_winner_is_player_name() -> None:
    """Test that winner field contains player1_name when player1 wins."""
    record: MatchRecord = {
        "match_id": 33333,
        "tournament_id": 11593,
        "tournament_name": "Mens Australian Open 2026",
        "round": "Final",
        "player1_name": "Ali Farag",
        "player1_id": 42,
        "player1_country": "EGY",
        "player1_seeding": "1",
        "player2_name": "Paul Coll",
        "player2_id": 57,
        "player2_country": "NZL",
        "player2_seeding": "2",
        "winner": "Ali Farag",
        "scores": "11-9, 9-11, 11-7, 11-8",
        "duration_minutes": 68,
        "source": "squashinfo",
    }

    assert record["winner"] == record["player1_name"]
