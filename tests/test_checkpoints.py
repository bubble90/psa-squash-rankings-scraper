"""
Test suite for checkpoint functionality in PSA Squash scraper.
"""

import json
import pytest
from pathlib import Path
from api_scraper import save_checkpoint, load_checkpoint, clear_checkpoint


def test_save_checkpoint(tmp_path: Path,
                         monkeypatch: pytest.MonkeyPatch
                         ) -> None:
    """Test that checkpoints are saved correctly."""
    monkeypatch.setattr("api_scraper.CHECKPOINT_DIR", tmp_path)

    test_data = [
        {"rank": 1, "player": "Ali Farag", "tournaments": 12, "points": 20000},
        {"rank": 2, "player": "Paul Coll", "tournaments": 10, "points": 18000},
    ]

    save_checkpoint("male", 5, test_data)

    checkpoint_file = tmp_path / "male_checkpoint.json"
    assert checkpoint_file.exists()

    with open(checkpoint_file, "r") as f:
        saved_data = json.load(f)

    assert saved_data["gender"] == "male"
    assert saved_data["last_page"] == 5
    assert saved_data["total_players"] == 2
    assert saved_data["players"] == test_data


def test_load_checkpoint_exists(tmp_path: Path,
                         monkeypatch: pytest.MonkeyPatch
                         ) -> None:
    """Test loading an existing checkpoint."""
    monkeypatch.setattr("api_scraper.CHECKPOINT_DIR", tmp_path)

    test_data = [
        {"rank": 1, "player": "Ali Farag", "tournaments": 12, "points": 20000},
        {"rank": 2, "player": "Paul Coll", "tournaments": 10, "points": 18000},
    ]

    save_checkpoint("male", 5, test_data)
    loaded = load_checkpoint("male")

    assert loaded is not None
    assert loaded["gender"] == "male"
    assert loaded["last_page"] == 5
    assert loaded["total_players"] == 2
    assert loaded["players"] == test_data


def test_load_checkpoint_not_exists(tmp_path: Path,
                         monkeypatch: pytest.MonkeyPatch
                         ) -> None:
    """Test loading checkpoint when file doesn't exist."""
    monkeypatch.setattr("api_scraper.CHECKPOINT_DIR", tmp_path)

    result = load_checkpoint("female")
    assert result is None


def test_clear_checkpoint(tmp_path: Path,
                         monkeypatch: pytest.MonkeyPatch
                         ) -> None:
    """Test that checkpoints are cleared correctly."""
    monkeypatch.setattr("api_scraper.CHECKPOINT_DIR", tmp_path)

    test_data = [{"rank": 1, "player": "Test", "tournaments": 5, "points": 1000}]
    save_checkpoint("male", 1, test_data)

    checkpoint_file = tmp_path / "male_checkpoint.json"
    assert checkpoint_file.exists()

    clear_checkpoint("male")
    assert not checkpoint_file.exists()


def test_clear_checkpoint_not_exists(tmp_path: Path,
                         monkeypatch: pytest.MonkeyPatch
                         ) -> None:
    """Test clearing checkpoint when file doesn't exist (should not raise error)."""
    monkeypatch.setattr("api_scraper.CHECKPOINT_DIR", tmp_path)

    clear_checkpoint("female")


def test_save_checkpoint_female(tmp_path: Path,
                         monkeypatch: pytest.MonkeyPatch
                         ) -> None:
    """Test checkpoint for female rankings."""
    monkeypatch.setattr("api_scraper.CHECKPOINT_DIR", tmp_path)

    test_data = [
        {"rank": 1, "player": "Nour El Sherbini", "tournaments": 11, "points": 19000}
    ]

    save_checkpoint("female", 3, test_data)

    checkpoint_file = tmp_path / "female_checkpoint.json"
    assert checkpoint_file.exists()

    loaded = load_checkpoint("female")
    assert loaded is not None
    assert loaded["gender"] == "female"
    assert loaded["last_page"] == 3


def test_checkpoint_overwrites_existing(tmp_path: Path,
                         monkeypatch: pytest.MonkeyPatch
                         ) -> None:
    """Test that saving a checkpoint overwrites existing file."""
    monkeypatch.setattr("api_scraper.CHECKPOINT_DIR", tmp_path)

    data1 = [{"rank": 1, "player": "Player 1", "tournaments": 5, "points": 1000}]
    save_checkpoint("male", 1, data1)

    data2 = [
        {"rank": 1, "player": "Player 1", "tournaments": 5, "points": 1000},
        {"rank": 2, "player": "Player 2", "tournaments": 6, "points": 2000},
    ]
    save_checkpoint("male", 2, data2)

    loaded = load_checkpoint("male")
    assert loaded is not None
    assert loaded["last_page"] == 2
    assert loaded["total_players"] == 2


def test_checkpoint_empty_data(tmp_path: Path,
                         monkeypatch: pytest.MonkeyPatch
                         ) -> None:
    """Test saving checkpoint with empty data."""
    monkeypatch.setattr("api_scraper.CHECKPOINT_DIR", tmp_path)

    save_checkpoint("male", 0, [])

    loaded = load_checkpoint("male")
    assert loaded is not None
    assert loaded["total_players"] == 0
    assert loaded["players"] == []


def test_checkpoint_large_dataset(tmp_path: Path,
                         monkeypatch: pytest.MonkeyPatch
                         ) -> None:
    """Test checkpoint with large dataset."""
    monkeypatch.setattr("api_scraper.CHECKPOINT_DIR", tmp_path)

    large_data = [
        {"rank": i, "player": f"Player {i}", "tournaments": 10, "points": 10000 - i}
        for i in range(1, 501)
    ]

    save_checkpoint("male", 5, large_data)
    loaded = load_checkpoint("male")

    assert loaded is not None
    assert loaded["total_players"] == 500
    assert len(loaded["players"]) == 500
    assert loaded["players"][0]["rank"] == 1
    assert loaded["players"][-1]["rank"] == 500
