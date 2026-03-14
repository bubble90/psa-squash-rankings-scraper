"""
Scraper for squashinfo.com tournament and match data.

Fetches tournament listings from /results and match results from individual
event pages. Returns TournamentRecord and MatchRecord objects.
"""

import re
import itertools
import requests
from typing import Optional
from bs4 import BeautifulSoup

from psa_squash_rankings.schema import TournamentRecord, MatchRecord
from psa_squash_rankings.logger import get_logger
from psa_squash_rankings.config import (
    SQUASHINFO_BASE_URL,
    SQUASHINFO_TIMEOUT,
    USER_AGENTS,
)

USER_AGENT_CYCLE = itertools.cycle(USER_AGENTS)


def _make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    return session


def _parse_tournament_rows(soup: BeautifulSoup) -> list[TournamentRecord]:
    """Parse tournament rows from the /results page table."""
    tournaments: list[TournamentRecord] = []
    table = soup.find("table")
    if not table:
        return tournaments

    rows = table.find_all("tr")
    for row in rows[1:]:  # skip header row
        tds = row.find_all("td")
        if len(tds) < 4:
            continue

        tier = tds[0].get_text(strip=True)
        name_td = tds[1]
        link = name_td.find("a")
        if not link:
            continue

        href = link.get("href", "")
        id_match = re.match(r"/events/(\d+)-(.+)", href)
        if not id_match:
            continue

        event_id = int(id_match.group(1))
        slug = id_match.group(2)

        # "(M)" or "(W)" suffix on the td text indicates gender
        name_text = name_td.get_text(strip=True)
        gender_match = re.search(r"\(([MW])\)\s*$", name_text)
        gender = gender_match.group(1) if gender_match else None

        name = link.get_text(strip=True)
        location = tds[2].get_text(strip=True)
        date = tds[3].get_text(strip=True)

        tournaments.append(
            TournamentRecord(
                id=event_id,
                name=name,
                gender=gender,
                tier=tier,
                location=location,
                date=date,
                url=f"{SQUASHINFO_BASE_URL}/events/{event_id}-{slug}",
                source="squashinfo",
            )
        )

    return tournaments


def _parse_player_info(a_tag) -> dict:
    """Extract name, id, seeding, and country from a player <a> tag."""
    href = a_tag.get("href", "")
    player_id_match = re.match(r"/player/(\d+)-", href)
    player_id = int(player_id_match.group(1)) if player_id_match else None
    name = a_tag.get_text(strip=True)

    # Seeding is a text node immediately before the <a>: e.g. "\n    [1] "
    prev = a_tag.previous_sibling
    pre_text = str(prev) if prev else ""
    seeding_match = re.search(r"\[([^\]]+)\]", pre_text)
    seeding = seeding_match.group(1) if seeding_match else None

    # Country code is a text node immediately after </a>: e.g. " (NZL)\n"
    nxt = a_tag.next_sibling
    next_text = str(nxt) if nxt else ""
    country_match = re.search(r"\(([A-Z]{2,3})\)", next_text)
    country = country_match.group(1) if country_match else None

    return {"name": name, "id": player_id, "seeding": seeding, "country": country}


def _parse_match_row(
    tr, round_name: str, tournament_id: int, tournament_name: str
) -> Optional[MatchRecord]:
    """Parse a single match <tr> into a MatchRecord."""
    tr_id = tr.get("id", "")
    match_id_match = re.match(r"match_(\d+)", tr_id)
    if not match_id_match:
        return None
    match_id = int(match_id_match.group(1))

    tds = tr.find_all("td")
    scores: Optional[str] = None
    duration_minutes: Optional[int] = None
    completed = False

    if len(tds) == 1 and tds[0].get("colspan") == "2":
        # Upcoming/incomplete match — single td with both players and "v"
        players_td = tds[0]
    elif len(tds) == 2:
        # Completed match — indv_col_1 (players) + indv_col_2 (scores)
        players_td = tds[0]
        score_raw = tds[1].get_text(strip=True)
        if score_raw.lower() == "bye":
            return None
        duration_match = re.search(r"\((\d+)m\)", score_raw)
        duration_minutes = int(duration_match.group(1)) if duration_match else None
        scores = re.sub(r"\s*\(\d+m\)", "", score_raw).strip() or None
        completed = True
    else:
        return None

    player_links = players_td.find_all("a", class_="event_player")
    if len(player_links) != 2:
        return None

    p1 = _parse_player_info(player_links[0])
    p2 = _parse_player_info(player_links[1])

    # "bt" means player1 beat player2; "v" means not yet played
    full_text = players_td.get_text()
    winner: Optional[str] = (
        p1["name"] if completed and re.search(r"\bbt\b", full_text) else None
    )

    return MatchRecord(
        match_id=match_id,
        tournament_id=tournament_id,
        tournament_name=tournament_name,
        round=round_name,
        player1_name=p1["name"],
        player1_id=p1["id"],
        player1_country=p1["country"],
        player1_seeding=p1["seeding"],
        player2_name=p2["name"],
        player2_id=p2["id"],
        player2_country=p2["country"],
        player2_seeding=p2["seeding"],
        winner=winner,
        scores=scores,
        duration_minutes=duration_minutes,
        source="squashinfo",
    )


def _parse_tournament_name(soup: BeautifulSoup) -> str:
    """Extract tournament name from the event page <h1>."""
    h1 = soup.find("h1")
    return h1.get_text(strip=True) if h1 else ""


def get_recent_tournaments(max_pages: Optional[int] = 1) -> list[TournamentRecord]:
    """
    Scrape recent tournaments from squashinfo.com/results.

    Results are ordered newest-first. Each page contains ~20 tournaments.

    Parameters:
    - max_pages: number of pages to fetch (default 1 ≈ 20 most recent tournaments)

    Returns:
    - list[TournamentRecord]

    Raises:
    - requests.exceptions.RequestException: on network errors
    """
    logger = get_logger(__name__)
    logger.info(
        f"Fetching recent tournaments from squashinfo.com (max_pages={max_pages})"
    )

    all_tournaments: list[TournamentRecord] = []
    session = _make_session()

    try:
        page = 1
        while True:
            if max_pages and page > max_pages:
                break

            url = (
                f"{SQUASHINFO_BASE_URL}/results"
                if page == 1
                else f"{SQUASHINFO_BASE_URL}/results?start={page}"
            )
            session.headers["User-Agent"] = next(USER_AGENT_CYCLE)

            logger.info(f"Fetching tournaments page {page}...")
            try:
                response = session.get(url, timeout=SQUASHINFO_TIMEOUT)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed on page {page}: {e}")
                raise

            soup = BeautifulSoup(response.text, "lxml")
            tournaments = _parse_tournament_rows(soup)

            if not tournaments:
                logger.info("No more tournaments found")
                break

            all_tournaments.extend(tournaments)
            logger.info(
                f"Fetched {len(tournaments)} tournaments (total: {len(all_tournaments)})"
            )

            # Stop if there's no Next link
            page_nav = soup.find("div", class_="page_nav")
            if not page_nav:
                break
            has_next = any(
                a.get_text(strip=True) == "Next" for a in page_nav.find_all("a")
            )
            if not has_next:
                break

            page += 1
    finally:
        session.close()
        logger.debug("HTTP session closed")

    logger.info(f"Total tournaments fetched: {len(all_tournaments)}")
    return all_tournaments


def get_tournament_matches(event_id: int, slug: str) -> list[MatchRecord]:
    """
    Scrape match results for a specific tournament from squashinfo.com.

    Parameters:
    - event_id: numeric tournament ID (e.g. 11593)
    - slug: URL slug (e.g. 'mens-australian-open-2026')

    Returns:
    - list[MatchRecord]: all matches with scores, round, and player info.
      Upcoming (not yet played) matches are included with winner=None, scores=None.

    Raises:
    - requests.exceptions.RequestException: on network errors
    """
    logger = get_logger(__name__)
    logger.info(f"Fetching matches for event {event_id} ({slug})")

    url = f"{SQUASHINFO_BASE_URL}/events/{event_id}-{slug}"
    session = _make_session()
    session.headers["User-Agent"] = next(USER_AGENT_CYCLE)

    try:
        response = session.get(url, timeout=SQUASHINFO_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for event {event_id}: {e}")
        raise
    finally:
        session.close()
        logger.debug("HTTP session closed")

    soup = BeautifulSoup(response.text, "lxml")
    tournament_name = _parse_tournament_name(soup)

    results_div = soup.find("div", id="results")
    if not results_div:
        logger.warning(f"No results section found for event {event_id}")
        return []

    matches: list[MatchRecord] = []
    current_round = ""

    for tbody in results_div.find_all("tbody"):
        if tbody.get("data-type"):
            # Match rows
            for tr in tbody.find_all("tr"):
                match = _parse_match_row(tr, current_round, event_id, tournament_name)
                if match:
                    matches.append(match)
        else:
            # Round header (e.g. "Semi-finals:", "Quarter-finals:")
            match_type_td = tbody.find("td", class_="match_type")
            if match_type_td:
                current_round = match_type_td.get_text(strip=True).rstrip(":")

    logger.info(f"Fetched {len(matches)} matches for event {event_id}")
    return matches
