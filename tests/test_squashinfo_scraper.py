"""
Tests for squashinfo_scraper.py.

All HTTP calls are mocked — no real network requests are made.
"""

import pytest
import requests
from unittest.mock import MagicMock, patch

from psa_squash_rankings.squashinfo_scraper import (
    get_recent_tournaments,
    get_tournament_matches,
    get_player_recent_matches,
    get_player_recent_tournaments,
    _parse_tournament_rows,
    _parse_player_info,
    _parse_match_row,
    _parse_tournament_name,
    _parse_player_recent_match_row,
    _parse_player_tournament_rows,
    _find_table_by_headers,
)
from psa_squash_rankings.schema import (
    TournamentRecord,
    MatchRecord,
    PlayerRecentMatchRecord,
    PlayerRecentTournamentRecord,
)
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# HTML fixtures
# ---------------------------------------------------------------------------

RESULTS_PAGE_HTML = """
<html><body>
  <table style="width:100%">
    <tr>
      <th> </th><th>Name</th><th>Location</th><th>Date</th>
    </tr>
    <tr class="darkline">
      <td style="text-align: right">PSA World Tour Gold</td>
      <td><a href="/events/11593-mens-australian-open-2026">Squash Australian Open</a> (M)</td>
      <td>Brisbane, Australia</td>
      <td>15 Mar 2026</td>
    </tr>
    <tr class="lightline">
      <td style="text-align: right">PSA Challenger Tour 30</td>
      <td><a href="/events/11596-womens-calgary-squash-week-open-2026">Calgary Squash Week Open</a> (W)</td>
      <td>Calgary, Canada</td>
      <td>15 Mar 2026</td>
    </tr>
  </table>
  <div class="page_nav">
    <div style="float:left;">Events <strong>1-20</strong> out of <strong>11,745</strong></div>
    <div style="float:right;">
      <span><strong>1</strong></span>
      <a href="/results?start=2">2</a>
      <a href="/results?start=2">Next</a>
      <a href="/results?start=588">Last</a>
    </div>
  </div>
</body></html>
"""

RESULTS_PAGE_LAST_HTML = """
<html><body>
  <table style="width:100%">
    <tr><th> </th><th>Name</th><th>Location</th><th>Date</th></tr>
    <tr class="darkline">
      <td>PSA Bronze</td>
      <td><a href="/events/100-old-event">Old Event</a> (M)</td>
      <td>London, UK</td>
      <td>01 Jan 2020</td>
    </tr>
  </table>
  <div class="page_nav">
    <div style="float:right;">
      <span><strong>588</strong></span>
    </div>
  </div>
</body></html>
"""

EVENT_PAGE_HTML = """
<html><body>
  <div id="content">
    <h1>$131,000 Men's Squash Australian Open 2026, South Bank Piazza, Brisbane, Australia</h1>
    <h2>Actions: <a href="/history/38">Show history</a></h2>
    <h2>PSA World Tour Gold, 10 - 15 March 2026</h2>
    <div class="darkborder" id="results">
      <table border="0" cellpadding="2" cellspacing="0" style="width:100%">
        <tbody>
          <tr><td class="match_type" colspan="2">Semi-finals:</td></tr>
        </tbody>
        <tbody data-type="6">
          <tr class="darkline" id="match_274602">
            <td colspan="2">
              [1] <a class="event_player" href="/player/5974-paul-coll">Paul Coll</a> (NZL)
              v
              [4] <a class="event_player" href="/player/12607-jonah-bryant">Jonah Bryant</a> (ENG)
            </td>
          </tr>
        </tbody>
        <tbody>
          <tr><td colspan="2"> </td></tr>
          <tr><td class="match_type" colspan="2">Quarter-finals:</td></tr>
        </tbody>
        <tbody data-type="7">
          <tr class="darkline" id="match_274488">
            <td class="indv_col_1">
              [1] <a class="event_player" href="/player/5974-paul-coll">Paul Coll</a> (NZL)
              bt
              [9/16] <a class="event_player" href="/player/5701-auguste-dussourd">Auguste Dussourd</a> (FRA)
            </td>
            <td class="indv_col_2">11-5, 11-4, 11-5 (40m)</td>
          </tr>
          <tr class="lightline" id="match_274489">
            <td class="indv_col_1">
              [4] <a class="event_player" href="/player/12607-jonah-bryant">Jonah Bryant</a> (ENG)
              bt
              [9/16] <a class="event_player" href="/player/14055-melvil-scianimanico">Melvil Scianimanico</a> (FRA)
            </td>
            <td class="indv_col_2">11-1, 9-11, 11-8, 11-7 (66m)</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</body></html>
"""

EVENT_PAGE_BYE_HTML = """
<html><body>
  <h1>Test Event</h1>
  <div id="results">
    <table>
      <tbody>
        <tr><td class="match_type" colspan="2">1st Round:</td></tr>
      </tbody>
      <tbody data-type="12">
        <tr class="darkline" id="match_999">
          <td class="indv_col_1">
            [1] <a class="event_player" href="/player/1-player-a">Player A</a> (EGY)
            bt
            <a class="event_player" href="/player/2-player-b">Player B</a> (USA)
          </td>
          <td class="indv_col_2">bye</td>
        </tr>
      </tbody>
    </table>
  </div>
</body></html>
"""


# ---------------------------------------------------------------------------
# Unit tests: _parse_tournament_rows
# ---------------------------------------------------------------------------


class TestParseTournamentRows:
    def test_parses_two_rows(self):
        soup = BeautifulSoup(RESULTS_PAGE_HTML, "lxml")
        results = _parse_tournament_rows(soup)
        assert len(results) == 2

    def test_first_row_fields(self):
        soup = BeautifulSoup(RESULTS_PAGE_HTML, "lxml")
        t = _parse_tournament_rows(soup)[0]
        assert t["id"] == 11593
        assert t["name"] == "Squash Australian Open"
        assert t["gender"] == "M"
        assert t["tier"] == "PSA World Tour Gold"
        assert t["location"] == "Brisbane, Australia"
        assert t["date"] == "15 Mar 2026"
        assert "squashinfo.com/events/11593" in t["url"]
        assert t["source"] == "squashinfo"

    def test_second_row_gender_w(self):
        soup = BeautifulSoup(RESULTS_PAGE_HTML, "lxml")
        t = _parse_tournament_rows(soup)[1]
        assert t["gender"] == "W"
        assert t["id"] == 11596

    def test_empty_table(self):
        soup = BeautifulSoup(
            "<html><body><table><tr><th>Name</th></tr></table></body></html>", "lxml"
        )
        assert _parse_tournament_rows(soup) == []

    def test_no_table(self):
        soup = BeautifulSoup("<html><body><p>nothing</p></body></html>", "lxml")
        assert _parse_tournament_rows(soup) == []

    def test_row_without_link_skipped(self):
        html = """
        <table>
          <tr><th>h</th></tr>
          <tr class="darkline"><td>Gold</td><td>No link here</td><td>City</td><td>01 Jan 2026</td></tr>
        </table>"""
        soup = BeautifulSoup(html, "lxml")
        assert _parse_tournament_rows(soup) == []


# ---------------------------------------------------------------------------
# Unit tests: _parse_player_info
# ---------------------------------------------------------------------------


class TestParsePlayerInfo:
    def _make_td(self, html):
        soup = BeautifulSoup(html, "lxml")
        return soup.find("a", class_="event_player")

    def test_full_info(self):
        html = '<td>[1] <a class="event_player" href="/player/5974-paul-coll">Paul Coll</a> (NZL)</td>'
        a = self._make_td(html)
        info = _parse_player_info(a)
        assert info["name"] == "Paul Coll"
        assert info["id"] == 5974
        assert info["seeding"] == "1"
        assert info["country"] == "NZL"

    def test_fractional_seeding(self):
        html = '<td>[9/16] <a class="event_player" href="/player/5701-dussourd">Auguste Dussourd</a> (FRA)</td>'
        a = self._make_td(html)
        info = _parse_player_info(a)
        assert info["seeding"] == "9/16"
        assert info["country"] == "FRA"

    def test_no_seeding(self):
        html = '<td><a class="event_player" href="/player/100-player">Player X</a> (EGY)</td>'
        a = self._make_td(html)
        info = _parse_player_info(a)
        assert info["seeding"] is None

    def test_no_player_id_in_href(self):
        html = '<td><a class="event_player" href="/player/abc">Player X</a> (EGY)</td>'
        a = self._make_td(html)
        info = _parse_player_info(a)
        assert info["id"] is None


# ---------------------------------------------------------------------------
# Unit tests: _parse_match_row
# ---------------------------------------------------------------------------


class TestParseMatchRow:
    def _row(self, html):
        soup = BeautifulSoup(html, "lxml")
        return soup.find("tr")

    def test_completed_match(self):
        html = """
        <tr class="darkline" id="match_274488">
          <td class="indv_col_1">
            [1] <a class="event_player" href="/player/5974-paul-coll">Paul Coll</a> (NZL)
            bt
            [9/16] <a class="event_player" href="/player/5701-dussourd">Auguste Dussourd</a> (FRA)
          </td>
          <td class="indv_col_2">11-5, 11-4, 11-5 (40m)</td>
        </tr>"""
        tr = self._row(html)
        match = _parse_match_row(tr, "Quarter-finals", 11593, "Australian Open 2026")
        assert match is not None
        assert match["match_id"] == 274488
        assert match["round"] == "Quarter-finals"
        assert match["player1_name"] == "Paul Coll"
        assert match["player1_seeding"] == "1"
        assert match["player1_country"] == "NZL"
        assert match["player2_name"] == "Auguste Dussourd"
        assert match["player2_seeding"] == "9/16"
        assert match["winner"] == "Paul Coll"
        assert match["scores"] == "11-5, 11-4, 11-5"
        assert match["duration_minutes"] == 40
        assert match["source"] == "squashinfo"

    def test_upcoming_match(self):
        html = """
        <tr class="darkline" id="match_274602">
          <td colspan="2">
            [1] <a class="event_player" href="/player/5974-paul-coll">Paul Coll</a> (NZL)
            v
            [4] <a class="event_player" href="/player/12607-jonah-bryant">Jonah Bryant</a> (ENG)
          </td>
        </tr>"""
        tr = self._row(html)
        match = _parse_match_row(tr, "Semi-finals", 11593, "Australian Open 2026")
        assert match is not None
        assert match["winner"] is None
        assert match["scores"] is None
        assert match["duration_minutes"] is None

    def test_bye_skipped(self):
        html = """
        <tr id="match_999">
          <td class="indv_col_1">
            <a class="event_player" href="/player/1-a">A</a> (EGY)
            bt
            <a class="event_player" href="/player/2-b">B</a> (USA)
          </td>
          <td class="indv_col_2">bye</td>
        </tr>"""
        tr = self._row(html)
        assert _parse_match_row(tr, "1st Round", 1, "Test") is None

    def test_no_match_id_skipped(self):
        html = """
        <tr>
          <td class="indv_col_1">
            <a class="event_player" href="/player/1-a">A</a> (EGY)
            bt
            <a class="event_player" href="/player/2-b">B</a> (USA)
          </td>
          <td class="indv_col_2">11-5, 11-4 (20m)</td>
        </tr>"""
        tr = self._row(html)
        assert _parse_match_row(tr, "Final", 1, "Test") is None

    def test_match_without_duration(self):
        html = """
        <tr id="match_500">
          <td class="indv_col_1">
            <a class="event_player" href="/player/1-a">Player A</a> (EGY)
            bt
            <a class="event_player" href="/player/2-b">Player B</a> (USA)
          </td>
          <td class="indv_col_2">11-9, 11-7, 11-6</td>
        </tr>"""
        tr = self._row(html)
        match = _parse_match_row(tr, "Final", 1, "Test")
        assert match is not None
        assert match["duration_minutes"] is None
        assert match["scores"] == "11-9, 11-7, 11-6"


# ---------------------------------------------------------------------------
# Unit tests: _parse_tournament_name
# ---------------------------------------------------------------------------


class TestParseTournamentName:
    def test_extracts_h1(self):
        soup = BeautifulSoup(EVENT_PAGE_HTML, "lxml")
        name = _parse_tournament_name(soup)
        assert "Australian Open 2026" in name

    def test_no_h1_returns_empty(self):
        soup = BeautifulSoup("<html><body></body></html>", "lxml")
        assert _parse_tournament_name(soup) == ""


# ---------------------------------------------------------------------------
# Integration tests: get_recent_tournaments (mocked HTTP)
# ---------------------------------------------------------------------------


class TestGetRecentTournaments:
    def _mock_response(self, html: str, status_code: int = 200):
        mock = MagicMock()
        mock.status_code = status_code
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_returns_tournament_records(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            mock_session = MockSession.return_value.__enter__.return_value
            MockSession.return_value = mock_session
            mock_session.get.return_value = self._mock_response(RESULTS_PAGE_HTML)

            results = get_recent_tournaments(max_pages=1)

        assert len(results) == 2
        assert all(r["source"] == "squashinfo" for r in results)

    def test_result_type_is_tournament_record(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            mock_session = MockSession.return_value.__enter__.return_value
            MockSession.return_value = mock_session
            mock_session.get.return_value = self._mock_response(RESULTS_PAGE_HTML)

            results = get_recent_tournaments(max_pages=1)

        assert isinstance(results, list)
        assert all(isinstance(r, dict) for r in results)
        assert all("id" in r and "name" in r and "tier" in r for r in results)

    def test_stops_at_max_pages(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            mock_session = MockSession.return_value.__enter__.return_value
            MockSession.return_value = mock_session
            mock_session.get.return_value = self._mock_response(RESULTS_PAGE_HTML)

            get_recent_tournaments(max_pages=1)

        assert mock_session.get.call_count == 1

    def test_stops_when_no_next_link(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            mock_session = MockSession.return_value.__enter__.return_value
            MockSession.return_value = mock_session
            mock_session.get.return_value = self._mock_response(RESULTS_PAGE_LAST_HTML)

            results = get_recent_tournaments(max_pages=10)

        assert mock_session.get.call_count == 1
        assert len(results) == 1

    def test_network_error_propagates(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            mock_session = MockSession.return_value.__enter__.return_value
            MockSession.return_value = mock_session
            mock_session.get.side_effect = requests.exceptions.ConnectionError("down")

            with pytest.raises(requests.exceptions.ConnectionError):
                get_recent_tournaments(max_pages=1)

    def test_http_error_propagates(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            mock_session = MockSession.return_value.__enter__.return_value
            MockSession.return_value = mock_session
            mock_response = self._mock_response("", 429)
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "429"
            )
            mock_session.get.return_value = mock_response

            with pytest.raises(requests.exceptions.HTTPError):
                get_recent_tournaments(max_pages=1)


# ---------------------------------------------------------------------------
# Integration tests: get_tournament_matches (mocked HTTP)
# ---------------------------------------------------------------------------


class TestGetTournamentMatches:
    def _mock_response(self, html: str, status_code: int = 200):
        mock = MagicMock()
        mock.status_code = status_code
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_returns_match_records(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            mock_session = MockSession.return_value.__enter__.return_value
            MockSession.return_value = mock_session
            mock_session.get.return_value = self._mock_response(EVENT_PAGE_HTML)

            matches = get_tournament_matches(11593, "mens-australian-open-2026")

        assert len(matches) == 3  # 1 upcoming SF + 2 completed QFs

    def test_completed_match_has_winner_and_scores(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            mock_session = MockSession.return_value.__enter__.return_value
            MockSession.return_value = mock_session
            mock_session.get.return_value = self._mock_response(EVENT_PAGE_HTML)

            matches = get_tournament_matches(11593, "mens-australian-open-2026")

        completed = [m for m in matches if m["winner"] is not None]
        assert len(completed) == 2
        assert completed[0]["scores"] == "11-5, 11-4, 11-5"
        assert completed[0]["duration_minutes"] == 40

    def test_upcoming_match_has_no_winner(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            mock_session = MockSession.return_value.__enter__.return_value
            MockSession.return_value = mock_session
            mock_session.get.return_value = self._mock_response(EVENT_PAGE_HTML)

            matches = get_tournament_matches(11593, "mens-australian-open-2026")

        upcoming = [m for m in matches if m["winner"] is None]
        assert len(upcoming) == 1
        assert upcoming[0]["round"] == "Semi-finals"

    def test_round_names_assigned(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            mock_session = MockSession.return_value.__enter__.return_value
            MockSession.return_value = mock_session
            mock_session.get.return_value = self._mock_response(EVENT_PAGE_HTML)

            matches = get_tournament_matches(11593, "mens-australian-open-2026")

        rounds = {m["round"] for m in matches}
        assert "Semi-finals" in rounds
        assert "Quarter-finals" in rounds

    def test_byes_excluded(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            mock_session = MockSession.return_value.__enter__.return_value
            MockSession.return_value = mock_session
            mock_session.get.return_value = self._mock_response(EVENT_PAGE_BYE_HTML)

            matches = get_tournament_matches(1, "test-event")

        assert len(matches) == 0

    def test_no_results_div_returns_empty(self):
        html = "<html><body><h1>Test Event</h1><p>No results yet.</p></body></html>"
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            mock_session = MockSession.return_value.__enter__.return_value
            MockSession.return_value = mock_session
            mock_session.get.return_value = self._mock_response(html)

            matches = get_tournament_matches(1, "test-event")

        assert matches == []

    def test_source_field_is_squashinfo(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            mock_session = MockSession.return_value.__enter__.return_value
            MockSession.return_value = mock_session
            mock_session.get.return_value = self._mock_response(EVENT_PAGE_HTML)

            matches = get_tournament_matches(11593, "mens-australian-open-2026")

        assert all(m["source"] == "squashinfo" for m in matches)

    def test_tournament_id_set_on_matches(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            mock_session = MockSession.return_value.__enter__.return_value
            MockSession.return_value = mock_session
            mock_session.get.return_value = self._mock_response(EVENT_PAGE_HTML)

            matches = get_tournament_matches(11593, "mens-australian-open-2026")

        assert all(m["tournament_id"] == 11593 for m in matches)

    def test_network_error_propagates(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            mock_session = MockSession.return_value.__enter__.return_value
            MockSession.return_value = mock_session
            mock_session.get.side_effect = requests.exceptions.Timeout("timed out")

            with pytest.raises(requests.exceptions.Timeout):
                get_tournament_matches(11593, "mens-australian-open-2026")


# ---------------------------------------------------------------------------
# HTML fixtures: player profile page
# ---------------------------------------------------------------------------

# Mirrors the actual squashinfo.com player page structure:
#   matches table  : Date | Opponent | W/L | Event | Ctry | Rnd | Score | PSA
#   tournaments table: Date | Seeding | Event | Ctry | Tour | Round Reached
PLAYER_PAGE_HTML = """
<html><body>
  <h1>Paul Coll(New Zealand)</h1>
  <table>
    <tr>
      <th>Date</th><th>Opponent</th><th>W/L</th><th>Event</th>
      <th>Ctry</th><th>Rnd</th><th>Score</th><th>PSA</th>
    </tr>
    <tr class="darkline">
      <td>Mar 2026</td>
      <td><a href="/player/5701-auguste-dussourd">Auguste Dussourd</a></td>
      <td title="">W</td>
      <td><a href="/events/11593-mens-australian-open-2026">Australian Open</a></td>
      <td>AUS</td>
      <td><abbr title="Quarter-finals">qf</abbr></td>
      <td>11-5, 11-4, 11-5 (40m)</td>
      <td>Y</td>
    </tr>
    <tr class="lightline">
      <td>Mar 2026</td>
      <td><a href="/player/7363-henry-leung">Henry Leung</a></td>
      <td title="">W</td>
      <td><a href="/events/11593-mens-australian-open-2026">Australian Open</a></td>
      <td>AUS</td>
      <td><abbr title="2nd round">r2</abbr></td>
      <td>11-1, 11-5, 11-6 (35m)</td>
      <td>Y</td>
    </tr>
  </table>
  <table>
    <tr>
      <th>Date</th><th>Seeding</th><th>Event</th><th>Ctry</th>
      <th>Tour</th><th>Round Reached</th>
    </tr>
    <tr class="darkline">
      <td>Mar 2026</td><td>[1]</td>
      <td><a href="/events/11593-mens-australian-open-2026">Australian Open</a></td>
      <td>AUS</td>
      <td><span title="$131,000">PSA Tour</span></td>
      <td>Quarter-finals</td>
    </tr>
    <tr class="lightline b">
      <td>Mar 2026</td><td>[1]</td>
      <td><a href="/events/11586-mens-new-zealand-open-2026">New Zealand Open</a></td>
      <td>NZL</td>
      <td><span title="$105,000">PSA Tour</span></td>
      <td>Winner</td>
    </tr>
  </table>
</body></html>
"""

PLAYER_PAGE_NO_RESULTS_HTML = """
<html><body>
  <h1>New Player</h1>
  <p>No match history available.</p>
</body></html>
"""

PLAYER_PAGE_LOSS_HTML = """
<html><body>
  <h1>Auguste Dussourd(France)</h1>
  <table>
    <tr>
      <th>Date</th><th>Opponent</th><th>W/L</th><th>Event</th>
      <th>Ctry</th><th>Rnd</th><th>Score</th><th>PSA</th>
    </tr>
    <tr class="darkline">
      <td>Mar 2026</td>
      <td><a href="/player/5974-paul-coll">Paul Coll</a></td>
      <td title="">L</td>
      <td><a href="/events/11593-mens-australian-open-2026">Australian Open</a></td>
      <td>AUS</td>
      <td><abbr title="Quarter-finals">qf</abbr></td>
      <td>5-11, 4-11, 5-11 (40m)</td>
      <td>Y</td>
    </tr>
  </table>
</body></html>
"""


# ---------------------------------------------------------------------------
# Unit tests: _find_table_by_headers
# ---------------------------------------------------------------------------


class TestFindTableByHeaders:
    def test_finds_matches_table(self):
        soup = BeautifulSoup(PLAYER_PAGE_HTML, "lxml")
        table = _find_table_by_headers(soup, "Opponent", "W/L", "Score")
        assert table is not None

    def test_finds_tournaments_table(self):
        soup = BeautifulSoup(PLAYER_PAGE_HTML, "lxml")
        table = _find_table_by_headers(soup, "Seeding", "Round Reached")
        assert table is not None

    def test_missing_header_returns_none(self):
        soup = BeautifulSoup(PLAYER_PAGE_NO_RESULTS_HTML, "lxml")
        assert _find_table_by_headers(soup, "Opponent", "W/L") is None


# ---------------------------------------------------------------------------
# Unit tests: _parse_player_recent_match_row
# ---------------------------------------------------------------------------


class TestParsePlayerRecentMatchRow:
    def _data_row(self, html):
        """Return the first <tr> that is a data row (has <td> not <th>)."""
        soup = BeautifulSoup(html, "lxml")
        for tr in soup.find_all("tr"):
            if tr.find("td"):
                return tr
        return None

    def test_completed_win(self):
        html = """<table><tr>
          <td>Mar 2026</td>
          <td><a href="/player/5701-auguste-dussourd">Auguste Dussourd</a></td>
          <td title="">W</td>
          <td><a href="/events/11593-mens-australian-open-2026">Australian Open</a></td>
          <td>AUS</td>
          <td><abbr title="Quarter-finals">qf</abbr></td>
          <td>11-5, 11-4, 11-5 (40m)</td>
          <td>Y</td>
        </tr></table>"""
        tr = self._data_row(html)
        m = _parse_player_recent_match_row(tr)
        assert m is not None
        assert m["result"] == "W"
        assert m["opponent_name"] == "Auguste Dussourd"
        assert m["opponent_id"] == 5701
        assert m["opponent_country"] is None
        assert m["scores"] == "11-5, 11-4, 11-5"
        assert m["duration_minutes"] == 40
        assert m["tournament_id"] == 11593
        assert m["tournament_name"] == "Australian Open"
        assert m["round"] == "Quarter-finals"
        assert m["date"] == "Mar 2026"
        assert m["source"] == "squashinfo"

    def test_completed_loss(self):
        html = """<table><tr>
          <td>Mar 2026</td>
          <td><a href="/player/5974-paul-coll">Paul Coll</a></td>
          <td title="">L</td>
          <td><a href="/events/11593-mens-australian-open-2026">Australian Open</a></td>
          <td>AUS</td>
          <td><abbr title="Quarter-finals">qf</abbr></td>
          <td>5-11, 4-11, 5-11 (40m)</td>
          <td>Y</td>
        </tr></table>"""
        tr = self._data_row(html)
        m = _parse_player_recent_match_row(tr)
        assert m is not None
        assert m["result"] == "L"
        assert m["opponent_name"] == "Paul Coll"

    def test_round_from_abbr_title(self):
        html = """<table><tr>
          <td>Mar 2026</td>
          <td><a href="/player/1-opp">Opp</a></td>
          <td>W</td>
          <td><a href="/events/1-event">Event</a></td>
          <td>AUS</td>
          <td><abbr title="Semi-finals">sf</abbr></td>
          <td>11-5, 11-4 (30m)</td>
          <td>Y</td>
        </tr></table>"""
        tr = self._data_row(html)
        m = _parse_player_recent_match_row(tr)
        assert m is not None
        assert m["round"] == "Semi-finals"

    def test_score_without_duration(self):
        html = """<table><tr>
          <td>Jan 2026</td>
          <td><a href="/player/1-opp">Opp</a></td>
          <td>W</td>
          <td><a href="/events/1-event">Event</a></td>
          <td>USA</td>
          <td><abbr title="Final">F</abbr></td>
          <td>11-9, 11-7, 11-6</td>
          <td>Y</td>
        </tr></table>"""
        tr = self._data_row(html)
        m = _parse_player_recent_match_row(tr)
        assert m is not None
        assert m["duration_minutes"] is None
        assert m["scores"] == "11-9, 11-7, 11-6"

    def test_too_few_columns_returns_none(self):
        html = """<table><tr><td>Mar 2026</td><td>Opp</td></tr></table>"""
        tr = self._data_row(html)
        assert _parse_player_recent_match_row(tr) is None

    def test_no_opponent_link_returns_none(self):
        html = """<table><tr>
          <td>Mar 2026</td>
          <td>No Link Here</td>
          <td>W</td>
          <td><a href="/events/1-event">Event</a></td>
          <td>AUS</td>
          <td><abbr title="qf">qf</abbr></td>
          <td>11-5, 11-4 (20m)</td>
          <td>Y</td>
        </tr></table>"""
        tr = self._data_row(html)
        assert _parse_player_recent_match_row(tr) is None


# ---------------------------------------------------------------------------
# Unit tests: _parse_player_tournament_rows
# ---------------------------------------------------------------------------


class TestParsePlayerTournamentRows:
    def test_parses_two_rows(self):
        soup = BeautifulSoup(PLAYER_PAGE_HTML, "lxml")
        results = _parse_player_tournament_rows(soup, 5974)
        assert len(results) == 2

    def test_first_row_fields(self):
        soup = BeautifulSoup(PLAYER_PAGE_HTML, "lxml")
        t = _parse_player_tournament_rows(soup, 5974)[0]
        assert t["player_id"] == 5974
        assert t["tournament_id"] == 11593
        assert t["tournament_name"] == "Australian Open"
        assert t["tier"] == "PSA Tour"
        assert t["location"] == "AUS"
        assert t["date"] == "Mar 2026"
        assert t["round_reached"] == "Quarter-finals"
        assert t["source"] == "squashinfo"

    def test_second_row_winner(self):
        soup = BeautifulSoup(PLAYER_PAGE_HTML, "lxml")
        t = _parse_player_tournament_rows(soup, 5974)[1]
        assert t["round_reached"] == "Winner"
        assert t["tournament_id"] == 11586

    def test_no_matching_table_returns_empty(self):
        soup = BeautifulSoup(PLAYER_PAGE_NO_RESULTS_HTML, "lxml")
        assert _parse_player_tournament_rows(soup, 5974) == []


# ---------------------------------------------------------------------------
# Integration tests: get_player_recent_matches (mocked HTTP)
# ---------------------------------------------------------------------------


class TestGetPlayerRecentMatches:
    def _mock_response(self, html: str, status_code: int = 200):
        mock = MagicMock()
        mock.status_code = status_code
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_returns_match_records(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            MockSession.return_value = MockSession.return_value
            MockSession.return_value.get.return_value = self._mock_response(
                PLAYER_PAGE_HTML
            )
            matches = get_player_recent_matches(5974, "paul-coll")

        assert len(matches) == 2
        assert all(m["source"] == "squashinfo" for m in matches)
        assert all(m["player_id"] == 5974 for m in matches)

    def test_win_results(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            MockSession.return_value = MockSession.return_value
            MockSession.return_value.get.return_value = self._mock_response(
                PLAYER_PAGE_HTML
            )
            matches = get_player_recent_matches(5974, "paul-coll")

        assert all(m["result"] == "W" for m in matches)

    def test_loss_result(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            MockSession.return_value = MockSession.return_value
            MockSession.return_value.get.return_value = self._mock_response(
                PLAYER_PAGE_LOSS_HTML
            )
            matches = get_player_recent_matches(5701, "auguste-dussourd")

        assert len(matches) == 1
        assert matches[0]["result"] == "L"
        assert matches[0]["opponent_name"] == "Paul Coll"

    def test_no_results_div_returns_empty(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            MockSession.return_value = MockSession.return_value
            MockSession.return_value.get.return_value = self._mock_response(
                PLAYER_PAGE_NO_RESULTS_HTML
            )
            matches = get_player_recent_matches(5974, "paul-coll")

        assert matches == []

    def test_network_error_propagates(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            MockSession.return_value = MockSession.return_value
            MockSession.return_value.get.side_effect = requests.exceptions.Timeout(
                "timed out"
            )
            with pytest.raises(requests.exceptions.Timeout):
                get_player_recent_matches(5974, "paul-coll")


# ---------------------------------------------------------------------------
# Integration tests: get_player_recent_tournaments (mocked HTTP)
# ---------------------------------------------------------------------------


class TestGetPlayerRecentTournaments:
    def _mock_response(self, html: str, status_code: int = 200):
        mock = MagicMock()
        mock.status_code = status_code
        mock.text = html
        mock.raise_for_status = MagicMock()
        return mock

    def test_returns_tournament_records(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            MockSession.return_value = MockSession.return_value
            MockSession.return_value.get.return_value = self._mock_response(
                PLAYER_PAGE_HTML
            )
            tournaments = get_player_recent_tournaments(5974, "paul-coll")

        assert len(tournaments) == 2
        assert all(t["source"] == "squashinfo" for t in tournaments)
        assert all(t["player_id"] == 5974 for t in tournaments)

    def test_round_reached_values(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            MockSession.return_value = MockSession.return_value
            MockSession.return_value.get.return_value = self._mock_response(
                PLAYER_PAGE_HTML
            )
            tournaments = get_player_recent_tournaments(5974, "paul-coll")

        rounds = {t["round_reached"] for t in tournaments}
        assert "Quarter-finals" in rounds
        assert "Winner" in rounds

    def test_no_tournament_results_returns_empty(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            MockSession.return_value = MockSession.return_value
            MockSession.return_value.get.return_value = self._mock_response(
                PLAYER_PAGE_NO_RESULTS_HTML
            )
            tournaments = get_player_recent_tournaments(5974, "paul-coll")

        assert tournaments == []

    def test_network_error_propagates(self):
        with patch(
            "psa_squash_rankings.squashinfo_scraper.requests.Session"
        ) as MockSession:
            MockSession.return_value = MockSession.return_value
            MockSession.return_value.get.side_effect = (
                requests.exceptions.ConnectionError("down")
            )
            with pytest.raises(requests.exceptions.ConnectionError):
                get_player_recent_tournaments(5974, "paul-coll")

