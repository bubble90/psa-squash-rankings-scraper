"""
Test suite for HTML scraper functionality in PSA Squash scraper.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from html_scraper import scrape_rankings_html


@patch("html_scraper.requests.Session")
def test_scrape_rankings_html_success(mock_session_class):
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    """Test HTML scraper with valid table."""
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


    df = scrape_rankings_html()

    assert len(df) == 2
    assert df.iloc[0]["rank"] == "1"
    assert df.iloc[0]["player"] == "Ali Farag"
    assert df.iloc[0]["tournaments"] == "12"
    assert df.iloc[0]["points"] == "20000"
    assert df.iloc[1]["player"] == "Paul Coll"


@patch("html_scraper.requests.Session")
def test_scrape_rankings_html_removes_commas(mock_session_class):
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

    df = scrape_rankings_html()

    assert df.iloc[0]["points"] == "123456"
    assert "," not in df.iloc[0]["points"]


@patch("html_scraper.requests.Session")
def test_scrape_rankings_html_no_table(mock_session_class):
    """Test HTML scraper when table is not found."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_response = Mock()
    mock_response.text = "<html><body>No table here</body></html>"
    mock_response.raise_for_status = Mock()
    mock_session.get.return_value = mock_response

    with pytest.raises(ValueError, match="Could not find rankings table"):
        scrape_rankings_html()


@patch("html_scraper.requests.Session")
def test_scrape_rankings_html_empty_table(mock_session_class):
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

    df = scrape_rankings_html()

    assert len(df) == 0


@patch("html_scraper.requests.Session")
def test_scrape_rankings_html_skips_incomplete_rows(mock_session_class):
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

    df = scrape_rankings_html()

    assert len(df) == 2
    assert df.iloc[0]["player"] == "Ali Farag"
    assert df.iloc[1]["player"] == "Paul Coll"


@patch("html_scraper.requests.Session")
def test_scrape_rankings_html_strips_whitespace(mock_session_class):
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

    df = scrape_rankings_html()

    assert df.iloc[0]["rank"] == "1"
    assert df.iloc[0]["player"] == "Ali Farag"
    assert df.iloc[0]["tournaments"] == "12"
    assert df.iloc[0]["points"] == "20000"


@patch("html_scraper.requests.Session")
def test_scrape_rankings_html_network_error(mock_session_class):
    """Test HTML scraper handles network errors."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_session.get.side_effect = Exception("Network error")

    with pytest.raises(Exception, match="Network error"):
        scrape_rankings_html()


@patch("html_scraper.requests.Session")
def test_scrape_rankings_html_timeout(mock_session_class):
    """Test HTML scraper handles timeout errors."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    import requests

    mock_session.get.side_effect = requests.exceptions.Timeout("Request timeout")

    with pytest.raises(requests.exceptions.Timeout):
        scrape_rankings_html()


@patch("html_scraper.requests.Session")
def test_scrape_rankings_html_http_error(mock_session_class):
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


@patch("html_scraper.requests.Session")
def test_scrape_rankings_html_correct_url(mock_session_class):
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

    # Verify correct URL was called
    called_url = mock_session.get.call_args[0][0]
    assert called_url == "https://www.psasquashtour.com/rankings/"


@patch("html_scraper.requests.Session")
def test_scrape_rankings_html_user_agent_present(mock_session_class):
    """Test that User-Agent header is set."""
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


@patch("html_scraper.requests.Session")
def test_scrape_rankings_html_timeout_parameter(mock_session_class):
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


@patch("html_scraper.requests.Session")
def test_scrape_rankings_html_large_dataset(mock_session_class):
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

    df = scrape_rankings_html()

    assert len(df) == 100
    assert df.iloc[0]["player"] == "Player 1"
    assert df.iloc[99]["player"] == "Player 100"


@patch("html_scraper.requests.Session")
def test_scrape_rankings_html_special_characters(mock_session_class):
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

    df = scrape_rankings_html()

    assert len(df) == 2
    assert df.iloc[0]["player"] == "Mohamed ElShorbagy"
    assert df.iloc[1]["player"] == "Grégory Gaultier"
