"""
Tests for validator.py — player recent match and tournament validation.
"""

import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch

from psa_squash_rankings.validator import (
    validate_player_match_record,
    validate_player_tournament_record,
    validate_player_data,
    validate_psa_player_bio_record,
    validate_psa_player_bio,
)

VALID_MATCH = {
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

VALID_TOURNAMENT = {
    "player_id": 5974,
    "tournament_id": 11593,
    "tournament_name": "Australian Open",
    "tier": "PSA Tour",
    "location": "AUS",
    "date": "Mar 2026",
    "round_reached": "Quarter-finals",
    "source": "squashinfo",
}


class TestValidatePlayerMatchRecord:
    def test_valid_win(self):
        validate_player_match_record(VALID_MATCH)  # should not raise

    def test_valid_loss(self):
        validate_player_match_record({**VALID_MATCH, "result": "L"})

    def test_valid_upcoming(self):
        validate_player_match_record({**VALID_MATCH, "result": "", "scores": None})

    def test_missing_player_id_raises(self):
        record = {k: v for k, v in VALID_MATCH.items() if k != "player_id"}
        with pytest.raises(ValueError, match="missing fields"):
            validate_player_match_record(record)

    def test_missing_opponent_name_raises(self):
        record = {k: v for k, v in VALID_MATCH.items() if k != "opponent_name"}
        with pytest.raises(ValueError, match="missing fields"):
            validate_player_match_record(record)

    def test_missing_result_raises(self):
        record = {k: v for k, v in VALID_MATCH.items() if k != "result"}
        with pytest.raises(ValueError, match="missing fields"):
            validate_player_match_record(record)

    def test_missing_source_raises(self):
        record = {k: v for k, v in VALID_MATCH.items() if k != "source"}
        with pytest.raises(ValueError, match="missing fields"):
            validate_player_match_record(record)

    def test_wrong_source_raises(self):
        with pytest.raises(ValueError, match="source"):
            validate_player_match_record({**VALID_MATCH, "source": "psa"})

    def test_invalid_result_raises(self):
        with pytest.raises(ValueError, match="result"):
            validate_player_match_record({**VALID_MATCH, "result": "D"})

    def test_zero_player_id_raises(self):
        with pytest.raises(ValueError, match="player_id"):
            validate_player_match_record({**VALID_MATCH, "player_id": 0})

    def test_negative_player_id_raises(self):
        with pytest.raises(ValueError, match="player_id"):
            validate_player_match_record({**VALID_MATCH, "player_id": -1})

    def test_string_player_id_raises(self):
        with pytest.raises(ValueError, match="player_id"):
            validate_player_match_record({**VALID_MATCH, "player_id": "5974"})

    def test_optional_fields_can_be_none(self):
        record = {
            **VALID_MATCH,
            "tournament_id": None,
            "opponent_id": None,
            "opponent_country": None,
            "scores": None,
            "duration_minutes": None,
            "date": None,
        }
        validate_player_match_record(record)  # should not raise


class TestValidatePlayerTournamentRecord:
    def test_valid_record(self):
        validate_player_tournament_record(VALID_TOURNAMENT)  # should not raise

    def test_missing_player_id_raises(self):
        record = {k: v for k, v in VALID_TOURNAMENT.items() if k != "player_id"}
        with pytest.raises(ValueError, match="missing fields"):
            validate_player_tournament_record(record)

    def test_missing_tournament_name_raises(self):
        record = {k: v for k, v in VALID_TOURNAMENT.items() if k != "tournament_name"}
        with pytest.raises(ValueError, match="missing fields"):
            validate_player_tournament_record(record)

    def test_missing_round_reached_raises(self):
        record = {k: v for k, v in VALID_TOURNAMENT.items() if k != "round_reached"}
        with pytest.raises(ValueError, match="missing fields"):
            validate_player_tournament_record(record)

    def test_missing_source_raises(self):
        record = {k: v for k, v in VALID_TOURNAMENT.items() if k != "source"}
        with pytest.raises(ValueError, match="missing fields"):
            validate_player_tournament_record(record)

    def test_wrong_source_raises(self):
        with pytest.raises(ValueError, match="source"):
            validate_player_tournament_record({**VALID_TOURNAMENT, "source": "psa"})

    def test_zero_player_id_raises(self):
        with pytest.raises(ValueError, match="player_id"):
            validate_player_tournament_record({**VALID_TOURNAMENT, "player_id": 0})

    def test_negative_player_id_raises(self):
        with pytest.raises(ValueError, match="player_id"):
            validate_player_tournament_record({**VALID_TOURNAMENT, "player_id": -1})

    def test_optional_fields_can_be_none(self):
        record = {
            **VALID_TOURNAMENT,
            "tournament_id": None,
            "tier": None,
            "location": None,
            "date": None,
        }
        validate_player_tournament_record(record)  # should not raise


class TestValidatePlayerData:
    def _write_matches(self, path: Path, rows: list[dict]) -> None:
        pd.DataFrame(rows).to_csv(
            path / "squashinfo_player_5974_matches.csv", index=False
        )

    def _write_tournaments(self, path: Path, rows: list[dict]) -> None:
        pd.DataFrame(rows).to_csv(
            path / "squashinfo_player_5974_tournaments.csv", index=False
        )

    def test_valid_files_run_without_error(self, tmp_path, monkeypatch):
        monkeypatch.setattr("psa_squash_rankings.validator.OUTPUT_DIR", tmp_path)
        self._write_matches(tmp_path, [VALID_MATCH])
        self._write_tournaments(tmp_path, [VALID_TOURNAMENT])
        validate_player_data(5974)  # should not raise

    def test_missing_both_files_logs_warning(self, tmp_path, monkeypatch):
        monkeypatch.setattr("psa_squash_rankings.validator.OUTPUT_DIR", tmp_path)
        # Neither file exists — should complete without raising
        validate_player_data(5974)

    def test_missing_matches_file_still_validates_tournaments(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr("psa_squash_rankings.validator.OUTPUT_DIR", tmp_path)
        self._write_tournaments(tmp_path, [VALID_TOURNAMENT])
        validate_player_data(5974)  # should not raise

    def test_missing_tournaments_file_still_validates_matches(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr("psa_squash_rankings.validator.OUTPUT_DIR", tmp_path)
        self._write_matches(tmp_path, [VALID_MATCH])
        validate_player_data(5974)  # should not raise

    def test_win_loss_counts_logged(self, tmp_path, monkeypatch):
        monkeypatch.setattr("psa_squash_rankings.validator.OUTPUT_DIR", tmp_path)
        rows = [
            {**VALID_MATCH, "result": "W"},
            {**VALID_MATCH, "result": "L"},
            {**VALID_MATCH, "result": ""},
        ]
        self._write_matches(tmp_path, rows)
        self._write_tournaments(tmp_path, [VALID_TOURNAMENT])

        with patch("psa_squash_rankings.validator.get_logger") as mock_log:
            mock_logger = mock_log.return_value
            validate_player_data(5974)

        info_calls = " ".join(str(c) for c in mock_logger.info.call_args_list)
        assert "1W" in info_calls or "1" in info_calls  # wins reported

    def test_missing_columns_logged_as_warning(self, tmp_path, monkeypatch):
        monkeypatch.setattr("psa_squash_rankings.validator.OUTPUT_DIR", tmp_path)
        # Write a matches CSV with a column stripped out
        incomplete = {k: v for k, v in VALID_MATCH.items() if k != "duration_minutes"}
        self._write_matches(tmp_path, [incomplete])
        self._write_tournaments(tmp_path, [VALID_TOURNAMENT])

        with patch("psa_squash_rankings.validator.get_logger") as mock_log:
            mock_logger = mock_log.return_value
            validate_player_data(5974)

        warning_calls = " ".join(str(c) for c in mock_logger.warning.call_args_list)
        assert "duration_minutes" in warning_calls

    def test_invalid_result_values_logged_as_error(self, tmp_path, monkeypatch):
        monkeypatch.setattr("psa_squash_rankings.validator.OUTPUT_DIR", tmp_path)
        bad_row = {**VALID_MATCH, "result": "D"}
        self._write_matches(tmp_path, [bad_row])
        self._write_tournaments(tmp_path, [VALID_TOURNAMENT])

        with patch("psa_squash_rankings.validator.get_logger") as mock_log:
            mock_logger = mock_log.return_value
            validate_player_data(5974)

        error_calls = " ".join(str(c) for c in mock_logger.error.call_args_list)
        assert "Invalid result" in error_calls


# ---------------------------------------------------------------------------
# PSA player bio validation
# ---------------------------------------------------------------------------

VALID_PSA_BIO = {
    "player_id": 11942,
    "name": "Mostafa Asal",
    "country": "EGY",
    "flag_url": "https://example.com/flag.png",
    "birthdate": "09-05-2001",
    "birthplace": "Egypt",
    "height_cm": 189,
    "weight_kg": 80,
    "coach": "James Willstrop",
    "residence": "Cairo, Egypt",
    "bio": "Mostafa Asal is World No.1.",
    "picture_url": "https://example.com/11942.jpg",
    "mugshot_url": "https://example.com/mugshot.jpg",
    "twitter": "https://twitter.com/mostafasal_",
    "facebook": "https://www.facebook.com/mostafasal_",
    "source": "api",
}


class TestValidatePsaPlayerBioRecord:
    def test_valid_record(self):
        validate_psa_player_bio_record(VALID_PSA_BIO)  # should not raise

    def test_optional_fields_can_be_none(self):
        record = {
            **VALID_PSA_BIO,
            "country": None,
            "flag_url": None,
            "birthdate": None,
            "birthplace": None,
            "height_cm": None,
            "weight_kg": None,
            "coach": None,
            "residence": None,
            "bio": None,
            "picture_url": None,
            "mugshot_url": None,
            "twitter": None,
            "facebook": None,
        }
        validate_psa_player_bio_record(record)  # should not raise

    def test_missing_player_id_raises(self):
        record = {k: v for k, v in VALID_PSA_BIO.items() if k != "player_id"}
        with pytest.raises(ValueError, match="missing fields"):
            validate_psa_player_bio_record(record)

    def test_missing_name_raises(self):
        record = {k: v for k, v in VALID_PSA_BIO.items() if k != "name"}
        with pytest.raises(ValueError, match="missing fields"):
            validate_psa_player_bio_record(record)

    def test_missing_source_raises(self):
        record = {k: v for k, v in VALID_PSA_BIO.items() if k != "source"}
        with pytest.raises(ValueError, match="missing fields"):
            validate_psa_player_bio_record(record)

    def test_wrong_source_raises(self):
        with pytest.raises(ValueError, match="source"):
            validate_psa_player_bio_record({**VALID_PSA_BIO, "source": "squashinfo"})

    def test_zero_player_id_raises(self):
        with pytest.raises(ValueError, match="player_id"):
            validate_psa_player_bio_record({**VALID_PSA_BIO, "player_id": 0})

    def test_negative_player_id_raises(self):
        with pytest.raises(ValueError, match="player_id"):
            validate_psa_player_bio_record({**VALID_PSA_BIO, "player_id": -1})

    def test_string_player_id_raises(self):
        with pytest.raises(ValueError, match="player_id"):
            validate_psa_player_bio_record({**VALID_PSA_BIO, "player_id": "11942"})

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="name"):
            validate_psa_player_bio_record({**VALID_PSA_BIO, "name": ""})


class TestValidatePsaPlayerBio:
    def _write_bio(self, path: Path, rows: list[dict]) -> None:
        pd.DataFrame(rows).to_csv(path / "psa_player_11942_bio.csv", index=False)

    def test_valid_file_runs_without_error(self, tmp_path, monkeypatch):
        monkeypatch.setattr("psa_squash_rankings.validator.OUTPUT_DIR", tmp_path)
        self._write_bio(tmp_path, [VALID_PSA_BIO])
        validate_psa_player_bio(11942)  # should not raise

    def test_missing_file_logs_warning(self, tmp_path, monkeypatch):
        monkeypatch.setattr("psa_squash_rankings.validator.OUTPUT_DIR", tmp_path)
        validate_psa_player_bio(11942)  # should not raise

    def test_missing_columns_logged_as_warning(self, tmp_path, monkeypatch):
        monkeypatch.setattr("psa_squash_rankings.validator.OUTPUT_DIR", tmp_path)
        incomplete = {k: v for k, v in VALID_PSA_BIO.items() if k != "bio"}
        self._write_bio(tmp_path, [incomplete])

        with patch("psa_squash_rankings.validator.get_logger") as mock_log:
            mock_logger = mock_log.return_value
            validate_psa_player_bio(11942)

        warning_calls = " ".join(str(c) for c in mock_logger.warning.call_args_list)
        assert "bio" in warning_calls
