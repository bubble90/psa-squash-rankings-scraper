"""
Tests for cli.py.

All scraper calls are mocked — no real network requests are made.
OUTPUT_DIR is redirected to tmp_path for every test.
"""

import sys
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

from psa_squash_rankings.cli import main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(argv: list[str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> int:
    """Patch sys.argv and OUTPUT_DIR, then call main()."""
    monkeypatch.setattr(sys, "argv", ["psa-scrape"] + argv)
    monkeypatch.setattr("psa_squash_rankings.cli.OUTPUT_DIR", tmp_path)
    monkeypatch.setattr("psa_squash_rankings.config.OUTPUT_DIR", tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    return main()


SAMPLE_MATCH = {
    "match_id": 1,
    "tournament_id": 11593,
    "tournament_name": "Australian Open",
    "round": "Quarter-finals",
    "player1_name": "Paul Coll",
    "player1_id": 5974,
    "player1_country": "NZL",
    "player1_seeding": "1",
    "player2_name": "Auguste Dussourd",
    "player2_id": 5701,
    "player2_country": "FRA",
    "player2_seeding": "9/16",
    "winner": "Paul Coll",
    "scores": "11-5, 11-4, 11-5",
    "duration_minutes": 40,
    "source": "squashinfo",
}

SAMPLE_TOURNAMENT = {
    "id": 11593,
    "name": "Australian Open",
    "gender": "M",
    "tier": "PSA World Tour Gold",
    "location": "Brisbane, Australia",
    "date": "15 Mar 2026",
    "url": "https://www.squashinfo.com/events/11593-mens-australian-open-2026",
    "source": "squashinfo",
}

SAMPLE_PLAYER_MATCH = {
    "player_id": 5974,
    "tournament_id": 11593,
    "tournament_name": "Australian Open",
    "round": "Quarter-finals",
    "opponent_name": "Auguste Dussourd",
    "opponent_id": 5701,
    "opponent_country": None,
    "result": "W",
    "scores": "11-5, 11-4, 11-5",
    "duration_minutes": 40,
    "date": "Mar 2026",
    "source": "squashinfo",
}

SAMPLE_PLAYER_TOURNAMENT = {
    "player_id": 5974,
    "tournament_id": 11593,
    "tournament_name": "Australian Open",
    "tier": "PSA Tour",
    "location": "AUS",
    "date": "Mar 2026",
    "round_reached": "Quarter-finals",
    "source": "squashinfo",
}

SAMPLE_API_PLAYER = {
    "rank": 1,
    "player": "Paul Coll",
    "id": 5974,
    "tournaments": 10,
    "points": 18000,
    "height_cm": 185,
    "weight_kg": 80,
    "birthdate": "1992-06-14",
    "country": "New Zealand",
    "picture_url": None,
    "mugshot_url": None,
    "source": "api",
}


# ---------------------------------------------------------------------------
# rankings subcommand
# ---------------------------------------------------------------------------


class TestRankingsCommand:
    def test_creates_male_csv(self, tmp_path, monkeypatch):
        with patch(
            "psa_squash_rankings.cli.get_rankings", return_value=[SAMPLE_API_PLAYER]
        ):
            with patch("psa_squash_rankings.cli.export_to_csv"):
                code = _run(["rankings", "--gender", "male"], tmp_path, monkeypatch)
        assert code == 0

    def test_creates_female_csv(self, tmp_path, monkeypatch):
        with patch(
            "psa_squash_rankings.cli.get_rankings", return_value=[SAMPLE_API_PLAYER]
        ):
            with patch("psa_squash_rankings.cli.export_to_csv") as mock_export:
                code = _run(["rankings", "--gender", "female"], tmp_path, monkeypatch)
        assert code == 0
        filenames = [call.args[1] for call in mock_export.call_args_list]
        assert any("female" in f for f in filenames)

    def test_both_genders_calls_get_rankings_twice(self, tmp_path, monkeypatch):
        with patch(
            "psa_squash_rankings.cli.get_rankings", return_value=[SAMPLE_API_PLAYER]
        ) as mock_get:
            with patch("psa_squash_rankings.cli.export_to_csv"):
                _run(["rankings", "--gender", "both"], tmp_path, monkeypatch)
        assert mock_get.call_count == 2

    def test_api_failure_falls_back_to_html(self, tmp_path, monkeypatch):
        html_player = {
            "rank": 1,
            "player": "Paul Coll",
            "tournaments": 10,
            "points": 18000,
            "mugshot_url": None,
            "source": "html",
        }
        with patch(
            "psa_squash_rankings.cli.get_rankings", side_effect=Exception("API down")
        ):
            with patch(
                "psa_squash_rankings.cli.scrape_rankings_html",
                return_value=[html_player],
            ):
                with patch("psa_squash_rankings.cli.export_to_csv"):
                    code = _run(["rankings", "--gender", "male"], tmp_path, monkeypatch)
        assert code == 0

    def test_both_sources_fail_returns_1(self, tmp_path, monkeypatch):
        with patch(
            "psa_squash_rankings.cli.get_rankings", side_effect=Exception("API down")
        ):
            with patch(
                "psa_squash_rankings.cli.scrape_rankings_html",
                side_effect=Exception("HTML down"),
            ):
                code = _run(["rankings", "--gender", "male"], tmp_path, monkeypatch)
        assert code == 1

    def test_default_command_is_rankings(self, tmp_path, monkeypatch):
        with patch(
            "psa_squash_rankings.cli.get_rankings", return_value=[SAMPLE_API_PLAYER]
        ) as mock_get:
            with patch("psa_squash_rankings.cli.export_to_csv"):
                _run([], tmp_path, monkeypatch)
        assert mock_get.called


# ---------------------------------------------------------------------------
# tournaments subcommand
# ---------------------------------------------------------------------------


class TestTournamentsCommand:
    def test_creates_csv(self, tmp_path, monkeypatch):
        with patch(
            "psa_squash_rankings.cli.get_recent_tournaments",
            return_value=[SAMPLE_TOURNAMENT],
        ):
            code = _run(["tournaments"], tmp_path, monkeypatch)

        assert code == 0
        assert (tmp_path / "squashinfo_tournaments.csv").exists()

    def test_csv_content(self, tmp_path, monkeypatch):
        with patch(
            "psa_squash_rankings.cli.get_recent_tournaments",
            return_value=[SAMPLE_TOURNAMENT],
        ):
            _run(["tournaments"], tmp_path, monkeypatch)

        df = pd.read_csv(tmp_path / "squashinfo_tournaments.csv")
        assert len(df) == 1
        assert df.iloc[0]["name"] == "Australian Open"
        assert df.iloc[0]["id"] == 11593

    def test_max_pages_passed_through(self, tmp_path, monkeypatch):
        with patch(
            "psa_squash_rankings.cli.get_recent_tournaments",
            return_value=[SAMPLE_TOURNAMENT],
        ) as mock_get:
            _run(["tournaments", "--max-pages", "3"], tmp_path, monkeypatch)

        mock_get.assert_called_once_with(max_pages=3)

    def test_empty_results_returns_1(self, tmp_path, monkeypatch):
        with patch("psa_squash_rankings.cli.get_recent_tournaments", return_value=[]):
            code = _run(["tournaments"], tmp_path, monkeypatch)
        assert code == 1

    def test_scraper_exception_returns_1(self, tmp_path, monkeypatch):
        with patch(
            "psa_squash_rankings.cli.get_recent_tournaments",
            side_effect=Exception("network error"),
        ):
            code = _run(["tournaments"], tmp_path, monkeypatch)
        assert code == 1


class TestMatchesCommand:
    def test_creates_csv(self, tmp_path, monkeypatch):
        with patch(
            "psa_squash_rankings.cli.get_tournament_matches",
            return_value=[SAMPLE_MATCH],
        ):
            code = _run(
                [
                    "matches",
                    "--event-id",
                    "11593",
                    "--slug",
                    "mens-australian-open-2026",
                ],
                tmp_path,
                monkeypatch,
            )

        assert code == 0
        assert (tmp_path / "squashinfo_matches_11593.csv").exists()

    def test_csv_content(self, tmp_path, monkeypatch):
        with patch(
            "psa_squash_rankings.cli.get_tournament_matches",
            return_value=[SAMPLE_MATCH],
        ):
            _run(
                [
                    "matches",
                    "--event-id",
                    "11593",
                    "--slug",
                    "mens-australian-open-2026",
                ],
                tmp_path,
                monkeypatch,
            )

        df = pd.read_csv(tmp_path / "squashinfo_matches_11593.csv")
        assert len(df) == 1
        assert df.iloc[0]["player1_name"] == "Paul Coll"
        assert df.iloc[0]["scores"] == "11-5, 11-4, 11-5"

    def test_event_id_and_slug_passed_through(self, tmp_path, monkeypatch):
        with patch(
            "psa_squash_rankings.cli.get_tournament_matches",
            return_value=[SAMPLE_MATCH],
        ) as mock_get:
            _run(
                [
                    "matches",
                    "--event-id",
                    "11593",
                    "--slug",
                    "mens-australian-open-2026",
                ],
                tmp_path,
                monkeypatch,
            )

        mock_get.assert_called_once_with(11593, "mens-australian-open-2026")

    def test_empty_results_returns_1(self, tmp_path, monkeypatch):
        with patch("psa_squash_rankings.cli.get_tournament_matches", return_value=[]):
            code = _run(
                ["matches", "--event-id", "1", "--slug", "event"],
                tmp_path,
                monkeypatch,
            )
        assert code == 1

    def test_scraper_exception_returns_1(self, tmp_path, monkeypatch):
        with patch(
            "psa_squash_rankings.cli.get_tournament_matches",
            side_effect=Exception("timeout"),
        ):
            code = _run(
                ["matches", "--event-id", "1", "--slug", "event"],
                tmp_path,
                monkeypatch,
            )
        assert code == 1


# ---------------------------------------------------------------------------
# player-history subcommand
# ---------------------------------------------------------------------------


class TestPlayerHistoryCommand:
    def test_creates_both_csvs(self, tmp_path, monkeypatch):
        with patch(
            "psa_squash_rankings.cli.get_player_recent_matches",
            return_value=[SAMPLE_PLAYER_MATCH],
        ):
            with patch(
                "psa_squash_rankings.cli.get_player_recent_tournaments",
                return_value=[SAMPLE_PLAYER_TOURNAMENT],
            ):
                code = _run(
                    ["player-history", "--player-id", "5974", "--slug", "paul-coll"],
                    tmp_path,
                    monkeypatch,
                )

        assert code == 0
        assert (tmp_path / "squashinfo_player_5974_matches.csv").exists()
        assert (tmp_path / "squashinfo_player_5974_tournaments.csv").exists()

    def test_matches_csv_content(self, tmp_path, monkeypatch):
        with patch(
            "psa_squash_rankings.cli.get_player_recent_matches",
            return_value=[SAMPLE_PLAYER_MATCH],
        ):
            with patch(
                "psa_squash_rankings.cli.get_player_recent_tournaments",
                return_value=[SAMPLE_PLAYER_TOURNAMENT],
            ):
                _run(
                    ["player-history", "--player-id", "5974", "--slug", "paul-coll"],
                    tmp_path,
                    monkeypatch,
                )

        df = pd.read_csv(tmp_path / "squashinfo_player_5974_matches.csv")
        assert len(df) == 1
        assert df.iloc[0]["opponent_name"] == "Auguste Dussourd"
        assert df.iloc[0]["result"] == "W"
        assert df.iloc[0]["round"] == "Quarter-finals"

    def test_tournaments_csv_content(self, tmp_path, monkeypatch):
        with patch(
            "psa_squash_rankings.cli.get_player_recent_matches",
            return_value=[SAMPLE_PLAYER_MATCH],
        ):
            with patch(
                "psa_squash_rankings.cli.get_player_recent_tournaments",
                return_value=[SAMPLE_PLAYER_TOURNAMENT],
            ):
                _run(
                    ["player-history", "--player-id", "5974", "--slug", "paul-coll"],
                    tmp_path,
                    monkeypatch,
                )

        df = pd.read_csv(tmp_path / "squashinfo_player_5974_tournaments.csv")
        assert len(df) == 1
        assert df.iloc[0]["tournament_name"] == "Australian Open"
        assert df.iloc[0]["round_reached"] == "Quarter-finals"

    def test_player_id_and_slug_passed_through(self, tmp_path, monkeypatch):
        with patch(
            "psa_squash_rankings.cli.get_player_recent_matches",
            return_value=[SAMPLE_PLAYER_MATCH],
        ) as mock_matches:
            with patch(
                "psa_squash_rankings.cli.get_player_recent_tournaments",
                return_value=[SAMPLE_PLAYER_TOURNAMENT],
            ) as mock_tournaments:
                _run(
                    ["player-history", "--player-id", "5974", "--slug", "paul-coll"],
                    tmp_path,
                    monkeypatch,
                )

        mock_matches.assert_called_once_with(5974, "paul-coll")
        mock_tournaments.assert_called_once_with(5974, "paul-coll")

    def test_no_matches_found_still_succeeds_if_tournaments_ok(
        self, tmp_path, monkeypatch
    ):
        with patch(
            "psa_squash_rankings.cli.get_player_recent_matches", return_value=[]
        ):
            with patch(
                "psa_squash_rankings.cli.get_player_recent_tournaments",
                return_value=[SAMPLE_PLAYER_TOURNAMENT],
            ):
                code = _run(
                    ["player-history", "--player-id", "5974", "--slug", "paul-coll"],
                    tmp_path,
                    monkeypatch,
                )

        assert code == 0
        assert not (tmp_path / "squashinfo_player_5974_matches.csv").exists()
        assert (tmp_path / "squashinfo_player_5974_tournaments.csv").exists()

    def test_matches_exception_returns_1_but_tournaments_still_run(
        self, tmp_path, monkeypatch
    ):
        with patch(
            "psa_squash_rankings.cli.get_player_recent_matches",
            side_effect=Exception("timeout"),
        ):
            with patch(
                "psa_squash_rankings.cli.get_player_recent_tournaments",
                return_value=[SAMPLE_PLAYER_TOURNAMENT],
            ):
                code = _run(
                    ["player-history", "--player-id", "5974", "--slug", "paul-coll"],
                    tmp_path,
                    monkeypatch,
                )

        assert code == 1
        assert (tmp_path / "squashinfo_player_5974_tournaments.csv").exists()

    def test_tournaments_exception_returns_1_but_matches_still_written(
        self, tmp_path, monkeypatch
    ):
        with patch(
            "psa_squash_rankings.cli.get_player_recent_matches",
            return_value=[SAMPLE_PLAYER_MATCH],
        ):
            with patch(
                "psa_squash_rankings.cli.get_player_recent_tournaments",
                side_effect=Exception("timeout"),
            ):
                code = _run(
                    ["player-history", "--player-id", "5974", "--slug", "paul-coll"],
                    tmp_path,
                    monkeypatch,
                )

        assert code == 1
        assert (tmp_path / "squashinfo_player_5974_matches.csv").exists()

    def test_both_empty_returns_0(self, tmp_path, monkeypatch):
        with patch(
            "psa_squash_rankings.cli.get_player_recent_matches", return_value=[]
        ):
            with patch(
                "psa_squash_rankings.cli.get_player_recent_tournaments", return_value=[]
            ):
                code = _run(
                    ["player-history", "--player-id", "5974", "--slug", "paul-coll"],
                    tmp_path,
                    monkeypatch,
                )
        assert code == 0
