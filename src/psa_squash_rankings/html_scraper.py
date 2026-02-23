"""
HTML-based scraper for PSA Squash Tour rankings.

WARNING: This is a FALLBACK scraper with degraded data quality.
Use only when the API scraper is unavailable.

Returns HtmlPlayerRecord objects which lack:
- Player IDs (cannot join with other datasets)
- Biographical data (height, weight, birthdate, country)
"""

import os
import itertools
import requests
from bs4 import BeautifulSoup
from psa_squash_rankings.logger import get_logger
from psa_squash_rankings.schema import HtmlPlayerRecord
from psa_squash_rankings.config import (
    HTML_BASE_URL,
    HTML_TIMEOUT,
    USER_AGENTS,
)


USER_AGENT_CYCLE = itertools.cycle(USER_AGENTS)


def scrape_rankings_html() -> list[HtmlPlayerRecord]:
    """
    Fallback scraper that parses the PSA rankings HTML table.

    WARNING: Returns degraded data without player IDs or biographical info.
    This should only be used when the API is unavailable.

    Returns:
    - list[HtmlPlayerRecord]: Limited player records (rank, name, tournaments, points only)

    Raises:
    - requests.exceptions.RequestException: On network errors
    - ValueError: If HTML table cannot be found or parsed

    Note: May return limited results if content is JS-rendered.
    """
    logger = get_logger(__name__)

    logger.warning(
        "Using HTML fallback scraper - data will be incomplete "
        "(no player IDs or biographical information)"
    )
    logger.info("Fetching rankings from HTML (fallback)...")
    logger.debug(f"Request URL: {HTML_BASE_URL}")

    proxy_url = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

    if proxies:
        logger.debug(f"Using proxy: {proxy_url}")

    session = requests.Session()

    session.headers.update({"User-Agent": next(USER_AGENT_CYCLE)})
    logger.debug(f"User-Agent: {session.headers['User-Agent']}")

    if proxies:
        session.proxies.update(proxies)

    try:
        try:
            response = session.get(HTML_BASE_URL, timeout=HTML_TIMEOUT)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            logger.error("HTML request timeout")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTML HTTP error: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"HTML request error: {e}")
            raise

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")

        if table is None:
            logger.error("Could not find rankings table in HTML")
            raise ValueError("Could not find rankings table in HTML.")

        tbody = table.find("tbody")

        if tbody:
            rows = tbody.find_all("tr")
        else:
            logger.info("No <tbody> found; searching for <tr> directly in <table>.")
            rows = table.find_all("tr", recursive=False)

        if not rows:
            logger.error("Rankings table found, but no rows (<tr>) were detected.")
            raise ValueError("The rankings table structure is empty or invalid.")

        data: list[HtmlPlayerRecord] = []

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 4:
                logger.warning(f"Skipping row with insufficient cells: {len(cells)}")
                continue

            try:
                rank = int(cells[0].get_text(strip=True))
                player = cells[1].get_text(strip=True)
                tournaments = int(cells[2].get_text(strip=True))
                points = int(cells[3].get_text(strip=True).replace(",", ""))
            except ValueError as e:
                logger.warning(f"Skipping row with invalid data: {e}")
                continue

            record: HtmlPlayerRecord = {
                "rank": rank,
                "player": player,
                "tournaments": tournaments,
                "points": points,
                "source": "html",
            }

            data.append(record)

        logger.info(f"Successfully scraped {len(data)} players from HTML")
        logger.warning(
            f"HTML scraper returned {len(data)} records WITHOUT player IDs or biographical data. "
            "This is degraded data suitable only for display purposes."
        )

        return data

    finally:
        session.close()
        logger.debug("HTTP session closed")


if __name__ == "__main__":
    logger = get_logger(__name__)
    try:
        result = scrape_rankings_html()
        logger.info(f"Successfully scraped {len(result)} players from HTML.")
        print(f"\nFirst 10 players (source: {result[0]['source']}):")
        for i, player in enumerate(result[:10], 1):
            print(f"{player['rank']}. {player['player']} - {player['points']} points")
    except Exception as e:
        logger.exception(f"HTML Scraper failed: {e}")
