"""
Test suite for HTML scraper functionality in PSA Squash scraper.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from psa_squash_rankings.html_scraper import scrape_rankings_html


@patch("psa_squash_rankings.html_scraper.requests.Session")
def test_scrape_rankings_html_success(mock_session_class: MagicMock) -> None:
    """Test HTML scraper with valid table."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_response = Mock()
    mock_response.text = """
    <html>
        <table>
            <tbody>
                <tr>
                    <td>1</td>
                    <td>Ali Farag</td>
                    <td>12</td>
                    <td>20,000</td>
                </tr>
                <tr>
                    <td>2</td>
                    <td>Paul Coll</td>
                    <td>10</td>
                    <td>18,000</td>
                </tr>
            </tbody>
        </table>
    </html>
    """
    mock_response.raise_for_status = Mock()
    mock_session.get.return_value = mock_response

    result = scrape_rankings_html()

    assert len(result) == 2
    assert result[0]["rank"] == 1
    assert result[0]["player"] == "Ali Farag"
    assert result[0]["tournaments"] == 12
    assert result[0]["points"] == 20000
    assert result[0]["source"] == "html"
    assert result[1]["player"] == "Paul Coll"
    assert result[1]["source"] == "html"
    mock_session.close.assert_called_once()


@patch("psa_squash_rankings.html_scraper.requests.Session")
def test_scrape_rankings_html_removes_commas(mock_session_class: MagicMock) -> None:
    """Test that commas are removed from points."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_response = Mock()
    mock_response.text = """
    <html>
        <table>
            <tbody>
                <tr>
                    <td>1</td>
                    <td>Test Player</td>
                    <td>15</td>
                    <td>123,456</td>
                </tr>
            </tbody>
        </table>
    </html>
    """
    mock_response.raise_for_status = Mock()
    mock_session.get.return_value = mock_response

    result = scrape_rankings_html()

    assert result[0]["points"] == 123456
    assert result[0]["source"] == "html"


@patch("psa_squash_rankings.html_scraper.requests.Session")
def test_scrape_rankings_html_no_table(mock_session_class: MagicMock) -> None:
    """Test HTML scraper when table is not found."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_response = Mock()
    mock_response.text = "<html><body>No table here</body></html>"
    mock_response.raise_for_status = Mock()
    mock_session.get.return_value = mock_response

    with pytest.raises(ValueError, match="Could not find rankings table"):
        scrape_rankings_html()

    mock_session.close.assert_called_once()


@patch("psa_squash_rankings.html_scraper.requests.Session")
def test_scrape_rankings_html_empty_table(mock_session_class: MagicMock) -> None:
    """Test HTML scraper with empty table."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_response = Mock()
    mock_response.text = """
    <html>
        <table>
            <tbody>
            </tbody>
        </table>
    </html>
    """
    mock_response.raise_for_status = Mock()
    mock_session.get.return_value = mock_response

    with pytest.raises(
        ValueError, match="The rankings table structure is empty or invalid"
    ):
        scrape_rankings_html()

    mock_session.close.assert_called_once()


@patch("psa_squash_rankings.html_scraper.requests.Session")
def test_scrape_rankings_html_skips_incomplete_rows(
    mock_session_class: MagicMock,
) -> None:
    """Test that rows with insufficient cells are skipped."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_response = Mock()
    mock_response.text = """
    <html>
        <table>
            <tbody>
                <tr>
                    <td>1</td>
                    <td>Ali Farag</td>
                    <td>12</td>
                    <td>20,000</td>
                </tr>
                <tr>
                    <td>2</td>
                    <td>Incomplete Row</td>
                </tr>
                <tr>
                    <td>3</td>
                    <td>Paul Coll</td>
                    <td>10</td>
                    <td>18,000</td>
                </tr>
            </tbody>
        </table>
    </html>
    """
    mock_response.raise_for_status = Mock()
    mock_session.get.return_value = mock_response

    result = scrape_rankings_html()

    assert len(result) == 2
    assert result[0]["player"] == "Ali Farag"
    assert result[1]["player"] == "Paul Coll"
    mock_session.close.assert_called_once()


@patch("psa_squash_rankings.html_scraper.requests.Session")
def test_scrape_rankings_html_strips_whitespace(mock_session_class: MagicMock) -> None:
    """Test that whitespace is stripped from cell text."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_response = Mock()
    mock_response.text = """
    <html>
        <table>
            <tbody>
                <tr>
                    <td>  1  </td>
                    <td>
                        Ali Farag
                    </td>
                    <td>  12  </td>
                    <td>  20,000  </td>
                </tr>
            </tbody>
        </table>
    </html>
    """
    mock_response.raise_for_status = Mock()
    mock_session.get.return_value = mock_response

    result = scrape_rankings_html()

    assert result[0]["rank"] == 1
    assert result[0]["player"] == "Ali Farag"
    assert result[0]["tournaments"] == 12
    assert result[0]["points"] == 20000
    mock_session.close.assert_called_once()


@patch("psa_squash_rankings.html_scraper.requests.Session")
def test_scrape_rankings_html_network_error(mock_session_class: MagicMock) -> None:
    """Test HTML scraper handles network errors."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_session.get.side_effect = Exception("Network error")

    with pytest.raises(Exception, match="Network error"):
        scrape_rankings_html()

    mock_session.close.assert_called_once()


@patch("psa_squash_rankings.html_scraper.requests.Session")
def test_scrape_rankings_html_timeout(mock_session_class: MagicMock) -> None:
    """Test HTML scraper handles timeout errors."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    import requests

    mock_session.get.side_effect = requests.exceptions.Timeout("Request timeout")

    with pytest.raises(requests.exceptions.Timeout):
        scrape_rankings_html()

    mock_session.close.assert_called_once()


@patch("psa_squash_rankings.html_scraper.requests.Session")
def test_scrape_rankings_html_http_error(mock_session_class: MagicMock) -> None:
    """Test HTML scraper handles HTTP errors."""
    import requests

    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
        "404 Not Found"
    )
    mock_session.get.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError):
        scrape_rankings_html()

    mock_session.close.assert_called_once()


@patch("psa_squash_rankings.html_scraper.requests.Session")
def test_scrape_rankings_html_correct_url(mock_session_class: MagicMock) -> None:
    """Test that the correct URL is called."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_response = Mock()
    mock_response.text = """
    <html>
        <table>
            <tbody>
                <tr>
                    <td>1</td>
                    <td>Test</td>
                    <td>5</td>
                    <td>1000</td>
                </tr>
            </tbody>
        </table>
    </html>
    """
    mock_response.raise_for_status = Mock()
    mock_session.get.return_value = mock_response

    scrape_rankings_html()

    called_url = mock_session.get.call_args[0][0]
    assert called_url == "https://www.psasquashtour.com/rankings/"
    mock_session.close.assert_called_once()


@patch("psa_squash_rankings.html_scraper.requests.Session")
def test_scrape_rankings_html_user_agent_rotation(
    mock_session_class: MagicMock,
) -> None:
    """Test that User-Agent is rotated."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_response = Mock()
    mock_response.text = """
    <html>
        <table>
            <tbody>
                <tr>
                    <td>1</td>
                    <td>Test</td>
                    <td>5</td>
                    <td>1000</td>
                </tr>
            </tbody>
        </table>
    </html>
    """
    mock_response.raise_for_status = Mock()
    mock_session.get.return_value = mock_response

    scrape_rankings_html()

    mock_session.headers.update.assert_called_once()
    call_args = mock_session.headers.update.call_args[0][0]
    assert "User-Agent" in call_args
    assert "Mozilla" in call_args["User-Agent"]
    mock_session.close.assert_called_once()


@patch("psa_squash_rankings.html_scraper.requests.Session")
def test_scrape_rankings_html_timeout_parameter(mock_session_class: MagicMock) -> None:
    """Test that timeout parameter is set."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_response = Mock()
    mock_response.text = """
    <html>
        <table>
            <tbody>
                <tr>
                    <td>1</td>
                    <td>Test</td>
                    <td>5</td>
                    <td>1000</td>
                </tr>
            </tbody>
        </table>
    </html>
    """
    mock_response.raise_for_status = Mock()
    mock_session.get.return_value = mock_response

    scrape_rankings_html()

    called_timeout = mock_session.get.call_args[1]["timeout"]
    assert called_timeout == 15
    mock_session.close.assert_called_once()


@patch("psa_squash_rankings.html_scraper.requests.Session")
def test_scrape_rankings_html_large_dataset(mock_session_class: MagicMock) -> None:
    """Test HTML scraper with many rows."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    rows_html = ""
    for i in range(1, 101):
        rows_html += f"""
        <tr>
            <td>{i}</td>
            <td>Player {i}</td>
            <td>10</td>
            <td>{10000 - i * 10}</td>
        </tr>
        """

    mock_response = Mock()
    mock_response.text = f"""
    <html>
        <table>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </html>
    """
    mock_response.raise_for_status = Mock()
    mock_session.get.return_value = mock_response

    result = scrape_rankings_html()

    assert len(result) == 100
    assert result[0]["player"] == "Player 1"
    assert result[99]["player"] == "Player 100"
    assert all(record["source"] == "html" for record in result)
    mock_session.close.assert_called_once()


@patch("psa_squash_rankings.html_scraper.requests.Session")
def test_scrape_rankings_html_special_characters(mock_session_class: MagicMock) -> None:
    """Test HTML scraper handles special characters in player names."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_response = Mock()
    mock_response.text = """
    <html>
        <table>
            <tbody>
                <tr>
                    <td>1</td>
                    <td>Mohamed ElShorbagy</td>
                    <td>12</td>
                    <td>20,000</td>
                </tr>
                <tr>
                    <td>2</td>
                    <td>Grégory Gaultier</td>
                    <td>10</td>
                    <td>18,000</td>
                </tr>
            </tbody>
        </table>
    </html>
    """
    mock_response.raise_for_status = Mock()
    mock_session.get.return_value = mock_response

    result = scrape_rankings_html()

    assert len(result) == 2
    assert result[0]["player"] == "Mohamed ElShorbagy"
    assert result[1]["player"] == "Grégory Gaultier"
    mock_session.close.assert_called_once()


@patch("psa_squash_rankings.html_scraper.requests.Session")
def test_scrape_rankings_html_returns_html_player_record_type(
    mock_session_class: MagicMock,
) -> None:
    """Test that return type is list[HtmlPlayerRecord]."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_response = Mock()
    mock_response.text = """
    <html>
        <table>
            <tbody>
                <tr>
                    <td>1</td>
                    <td>Ali Farag</td>
                    <td>12</td>
                    <td>20,000</td>
                </tr>
            </tbody>
        </table>
    </html>
    """
    mock_response.raise_for_status = Mock()
    mock_session.get.return_value = mock_response

    result = scrape_rankings_html()

    assert isinstance(result, list)
    assert len(result) == 1

    record = result[0]
    assert "rank" in record
    assert "player" in record
    assert "tournaments" in record
    assert "points" in record
    assert "source" in record
    assert record["source"] == "html"

    assert "id" not in record
    assert "height_cm" not in record
    assert "weight_kg" not in record
    assert "birthdate" not in record
    assert "country" not in record
    mock_session.close.assert_called_once()
