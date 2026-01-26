"""
Test suite for API scraper functionality in PSA Squash scraper.
"""

import pytest
from unittest.mock import Mock, patch
from api_scraper import get_rankings


@patch("api_scraper.requests.get")
def test_get_rankings_single_page(mock_get):
    """Test fetching a single page of rankings."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "players": [
            {
                "World Ranking": 1,
                "Name": "Ali Farag",
                "Id": 12345,
                "Tournaments": 12,
                "Total Points": 20000,
                "Birthdate": "1992-01-01",
                "Height": "180cm",
                "Weight": "75kg",
                "Country": "Egypt",
            },
            {
                "World Ranking": 2,
                "Name": "Paul Coll",
                "Id": 67890,
                "Tournaments": 10,
                "Total Points": 18000,
                "Birthdate": "1992-06-14",
                "Height": "185cm",
                "Weight": "80kg",
                "Country": "New Zealand",
            },
        ],
        "hasMore": False,
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    df = get_rankings("male", page_size=100, max_pages=1, resume=False)

    assert len(df) == 2
    assert df.iloc[0]["player"] == "Ali Farag"
    assert df.iloc[0]["points"] == 20000
    assert df.iloc[0]["id"] == 12345
    assert df.iloc[0]["birthdate"] == "1992-01-01"
    assert df.iloc[0]["height(cm)"] == 180
    assert df.iloc[0]["weight(kg)"] == 75
    assert df.iloc[0]["country"] == "Egypt"
    assert df.iloc[1]["player"] == "Paul Coll"
    assert df.iloc[1]["points"] == 18000


@patch("api_scraper.requests.get")
def test_get_rankings_with_missing_optional_fields(mock_get):
    """Test fetching rankings when optional fields are missing."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "players": [
            {
                "World Ranking": 1,
                "Name": "Ali Farag",
                "Id": 12345,
                "Tournaments": 12,
                "Total Points": 20000,
            },
        ],
        "hasMore": False,
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    df = get_rankings("male", page_size=100, max_pages=1, resume=False)

    assert len(df) == 1
    assert df.iloc[0]["birthdate"] == "N/A"
    assert df.iloc[0]["height(cm)"] == "N/A"
    assert df.iloc[0]["weight(kg)"] == "N/A"
    assert df.iloc[0]["country"] == "N/A"


@patch("api_scraper.requests.get")
def test_get_rankings_multiple_pages(mock_get):
    """Test fetching multiple pages with pagination."""
    page1_response = Mock()
    page1_response.json.return_value = {
        "players": [
            {
                "World Ranking": i,
                "Name": f"Player {i}",
                "Id": 1000 + i,
                "Tournaments": 10,
                "Total Points": 10000 - i * 100,
            }
            for i in range(1, 51)
        ],
        "hasMore": True,
    }
    page1_response.raise_for_status = Mock()

    page2_response = Mock()
    page2_response.json.return_value = {
        "players": [
            {
                "World Ranking": i,
                "Name": f"Player {i}",
                "Id": 1000 + i,
                "Tournaments": 10,
                "Total Points": 10000 - i * 100,
            }
            for i in range(51, 101)
        ],
        "hasMore": False,
    }
    page2_response.raise_for_status = Mock()

    mock_get.side_effect = [page1_response, page2_response]

    df = get_rankings("male", page_size=50, resume=False)

    assert len(df) == 100
    assert mock_get.call_count == 2


@patch("api_scraper.requests.get")
def test_get_rankings_empty_response(mock_get):
    """Test handling of empty API response."""
    mock_response = Mock()
    mock_response.json.return_value = {"players": [], "hasMore": False}
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    df = get_rankings("male", page_size=100, resume=False)

    assert len(df) == 0


@patch("api_scraper.requests.get")
def test_get_rankings_respects_max_pages(mock_get):
    """Test that max_pages parameter is respected."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "players": [
            {
                "World Ranking": i,
                "Name": f"Player {i}",
                "Id": 1000 + i,
                "Tournaments": 10,
                "Total Points": 10000,
            }
            for i in range(1, 11)
        ],
        "hasMore": True,
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    df = get_rankings("male", page_size=10, max_pages=3, resume=False)

    assert mock_get.call_count == 3
    assert len(df) == 30


@patch("api_scraper.requests.get")
def test_get_rankings_female(mock_get):
    """Test fetching female rankings."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "players": [
            {
                "World Ranking": 1,
                "Name": "Nour El Sherbini",
                "Id": 11111,
                "Tournaments": 11,
                "Total Points": 19000,
            }
        ],
        "hasMore": False,
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    df = get_rankings("female", page_size=100, resume=False)

    assert len(df) == 1
    assert df.iloc[0]["player"] == "Nour El Sherbini"

    called_url = mock_get.call_args[0][0]
    assert "/rankedplayers/female" in called_url


@patch("api_scraper.requests.get")
def test_get_rankings_network_error(mock_get):
    """Test handling of network errors."""
    mock_get.side_effect = Exception("Network error")

    with pytest.raises(Exception, match="Network error"):
        get_rankings("male", page_size=100, resume=False)


@patch("api_scraper.requests.get")
def test_get_rankings_http_error(mock_get):
    """Test handling of HTTP errors."""
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = Exception("404 Not Found")
    mock_get.return_value = mock_response

    with pytest.raises(Exception, match="404 Not Found"):
        get_rankings("male", page_size=100, resume=False)


@patch("api_scraper.requests.get")
def test_get_rankings_invalid_json(mock_get):
    """Test handling of invalid JSON response."""
    mock_response = Mock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="Invalid JSON"):
        get_rankings("male", page_size=100, resume=False)


@patch("api_scraper.requests.get")
def test_get_rankings_list_response(mock_get):
    """Test handling API response as a list (not dict)."""
    mock_response = Mock()
    mock_response.json.return_value = [
        {
            "World Ranking": 1,
            "Name": "Ali Farag",
            "Id": 12345,
            "Tournaments": 12,
            "Total Points": 20000,
        }
    ]
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    df = get_rankings("male", page_size=100, resume=False)

    assert len(df) == 1
    assert df.iloc[0]["player"] == "Ali Farag"


@patch("api_scraper.requests.get")
def test_get_rankings_stops_on_partial_page(mock_get):
    """Test scraper stops when partial page is returned."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "players": [
            {
                "World Ranking": i,
                "Name": f"Player {i}",
                "Id": 1000 + i,
                "Tournaments": 10,
                "Total Points": 10000,
            }
            for i in range(1, 26)
        ],
        "hasMore": True,
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    df = get_rankings("male", page_size=50, resume=False)

    assert len(df) == 25
    assert mock_get.call_count == 1


@patch("api_scraper.requests.get")
def test_get_rankings_uses_data_key(mock_get):
    """Test API response using 'data' key instead of 'players'."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": [
            {
                "World Ranking": 1,
                "Name": "Ali Farag",
                "Id": 12345,
                "Tournaments": 12,
                "Total Points": 20000,
            }
        ],
        "hasMore": False,
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    df = get_rankings("male", page_size=100, resume=False)

    assert len(df) == 1
    assert df.iloc[0]["player"] == "Ali Farag"


@patch("api_scraper.requests.get")
def test_get_rankings_custom_page_size(mock_get):
    """Test custom page size parameter."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "players": [
            {
                "World Ranking": i,
                "Name": f"Player {i}",
                "Id": 1000 + i,
                "Tournaments": 10,
                "Total Points": 10000,
            }
            for i in range(1, 6)
        ],
        "hasMore": False,
    }
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    df = get_rankings("male", page_size=5, resume=False)

    called_url = mock_get.call_args[0][0]
    assert "pageSize=5" in called_url


@patch("api_scraper.requests.get")
def test_get_rankings_pagination_url_format(mock_get):
    """Test that pagination URLs are formatted correctly."""
    page1_response = Mock()
    page1_response.json.return_value = {
        "players": [
            {
                "World Ranking": 1,
                "Name": "Player 1",
                "Id": 1001,
                "Tournaments": 10,
                "Total Points": 10000,
            }
        ],
        "hasMore": True,
    }
    page1_response.raise_for_status = Mock()

    page2_response = Mock()
    page2_response.json.return_value = {
        "players": [
            {
                "World Ranking": 2,
                "Name": "Player 2",
                "Id": 1002,
                "Tournaments": 10,
                "Total Points": 9000,
            }
        ],
        "hasMore": False,
    }
    page2_response.raise_for_status = Mock()

    mock_get.side_effect = [page1_response, page2_response]

    df = get_rankings("male", page_size=1, resume=False)

    assert mock_get.call_count == 2

    call1_url = mock_get.call_args_list[0][0][0]
    call2_url = mock_get.call_args_list[1][0][0]

    assert "page=1" in call1_url
    assert "page=2" in call2_url
    assert "pageSize=1" in call1_url
    assert "pageSize=1" in call2_url
