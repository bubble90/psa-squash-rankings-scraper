"""
HTML-based scraper for PSA Squash Tour rankings.
"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
from logger import get_logger

logger = get_logger(__name__)


def scrape_rankings_html():
    """
    Fallback scraper that parses the PSA rankings HTML table.
    Note: May return limited results if content is JS-rendered.
    """
    url = "https://www.psasquashtour.com/rankings/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    }

    logger.info("Fetching rankings from HTML (fallback)...")
    logger.debug(f"Request URL: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=15)
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

    rows = table.find("tbody").find_all("tr")
    data = []

    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 4:
            logger.warning(f"Skipping row with insufficient cells: {len(cells)}")
            continue

        data.append({
            "rank": cells[0].get_text(strip=True),
            "player": cells[1].get_text(strip=True),
            "tournaments": cells[2].get_text(strip=True),
            "points": cells[3].get_text(strip=True).replace(",", ""),
        })

    logger.info(f"Successfully scraped {len(data)} players from HTML")
    return pd.DataFrame(data)


if __name__ == "__main__":
    try:
        df = scrape_rankings_html()
        logger.info(f"Successfully scraped {len(df)} players from HTML.")
        print(df.head())
    except Exception as e:
        logger.exception(f"HTML Scraper failed: {e}")