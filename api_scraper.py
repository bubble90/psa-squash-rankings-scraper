"""
API-based scraper for PSA Squash Tour rankings.

Fetches ranking data directly from the PSA backend API.
"""

import os
import json
import itertools
import requests
import pandas as pd
from data_parser import parse_api_player
from logger import get_logger
from config import (
    API_BASE_URL,
    API_TIMEOUT,
    USER_AGENTS,
    CHECKPOINT_DIR,
)


USER_AGENT_CYCLE = itertools.cycle(USER_AGENTS)


def save_checkpoint(gender, page, data):
    """
    Save a checkpoint of the current scraping progress.

    Parameters:
    - gender: 'male' or 'female'
    - page: current page number
    - data: list of player dictionaries collected so far
    """
    logger = get_logger(__name__)

    checkpoint_file = CHECKPOINT_DIR / f"{gender}_checkpoint.json"
    checkpoint_data = {
        "gender": gender,
        "last_page": page,
        "total_players": len(data),
        "players": data,
    }

    try:
        with open(checkpoint_file, "w") as f:
            json.dump(checkpoint_data, f, indent=2)
        logger.info(f"Checkpoint saved: {len(data)} players, page {page}")
    except Exception as e:
        logger.error(f"Failed to save checkpoint: {e}")
        raise


def load_checkpoint(gender):
    """
    Load a checkpoint for resumable scraping.

    Returns:
    - dict with 'last_page' and 'players' if checkpoint exists
    - None if no checkpoint found
    """
    logger = get_logger(__name__)
    checkpoint_file = CHECKPOINT_DIR / f"{gender}_checkpoint.json"

    if checkpoint_file.exists():
        try:
            with open(checkpoint_file, "r") as f:
                data = json.load(f)
            logger.info(
                f"Resuming from checkpoint: {data['total_players']} players, page {data['last_page']}"
            )
            return data
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None

    logger.debug(f"No checkpoint found for {gender}")
    return None


def clear_checkpoint(gender):
    """
    Remove checkpoint file after successful completion.
    """
    logger = get_logger(__name__)

    checkpoint_file = CHECKPOINT_DIR / f"{gender}_checkpoint.json"
    if checkpoint_file.exists():
        try:
            checkpoint_file.unlink()
            logger.info(f"Checkpoint cleared for {gender}")
        except Exception as e:
            logger.error(f"Failed to clear checkpoint: {e}")


def get_rankings(gender="male", page_size=100, max_pages=None, resume=True):
    """
    Fetches PSA rankings for a specific gender with pagination support.

    Parameters:
    - gender: 'male' or 'female'
    - page_size: number of results per page (default 100)
    - max_pages: maximum number of pages to fetch (None = all)
    - resume: whether to resume from checkpoint if available

    Returns:
    - pandas DataFrame with all ranking data
    """
    logger = get_logger(__name__)

    logger.info(
        f"Starting {gender} rankings scrape (page_size={page_size}, max_pages={max_pages}, resume={resume})"
    )

    all_players = []
    start_page = 1

    if resume:
        checkpoint = load_checkpoint(gender)
        if checkpoint:
            all_players = checkpoint["players"]
            start_page = checkpoint["last_page"] + 1
            logger.info(f"Resuming scrape from page {start_page}")

    base_url = f"{API_BASE_URL}/{gender}"

    proxy_url = os.getenv("HTTP_PROXY") or os.getenv("HTTPS_PROXY")
    proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None

    if proxies:
        logger.debug(f"Using proxy: {proxy_url}")

    session = requests.Session()
    session.headers.update({"Accept": "application/json"})

    if proxies:
        session.proxies.update(proxies)

    page = start_page

    try:
        while True:
            if max_pages and page > max_pages:
                logger.info(f"Reached maximum page limit: {max_pages}")
                break

            url = f"{base_url}?page={page}&pageSize={page_size}"

            session.headers["User-Agent"] = next(USER_AGENT_CYCLE)

            logger.info(f"Fetching {gender} rankings - Page {page}...")
            logger.debug(f"Request URL: {url}")
            logger.debug(f"User-Agent: {session.headers['User-Agent']}")

            try:
                response = session.get(url, timeout=API_TIMEOUT)
                response.raise_for_status()
            except requests.exceptions.Timeout:
                logger.error(f"Request timeout on page {page}")
                raise
            except requests.exceptions.HTTPError as e:
                logger.error(f"HTTP error on page {page}: {e}")
                raise
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on page {page}: {e}")
                raise

            raw_data = response.json()
            logger.debug(
                f"Response keys: {raw_data.keys() if isinstance(raw_data, dict) else 'list response'}"
            )

            if isinstance(raw_data, dict):
                players_data = raw_data.get("players", raw_data.get("data", []))
                has_more = raw_data.get("hasMore", False)
            else:
                players_data = raw_data
                has_more = len(players_data) == page_size

            if not players_data:
                logger.info(f"No more data returned on page {page}")
                break

            parsed_players = [parse_api_player(player) for player in players_data]
            all_players.extend(parsed_players)

            logger.info(
                f"Fetched {len(parsed_players)} players (Total so far: {len(all_players)})"
            )

            save_checkpoint(gender, page, all_players)

            if not has_more or len(parsed_players) < page_size:
                logger.info("Reached last page")
                break

            page += 1

    except Exception as e:
        logger.error(f"Error on page {page}: {e}")
        logger.info(
            f"Progress saved in checkpoint. Run again to resume from page {page + 1}"
        )
        raise

    finally:
        session.close()
        logger.debug("HTTP session closed")

    clear_checkpoint(gender)

    logger.info(f"Successfully scraped {len(all_players)} {gender} players")
    return pd.DataFrame(all_players)


if __name__ == "__main__":
    logger = get_logger(__name__)
    try:
        df = get_rankings("male", page_size=50, resume=True)
        logger.info(f"Total players fetched: {len(df)}")
        print("\nFirst 10 players:")
        print(df.head(10))
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
