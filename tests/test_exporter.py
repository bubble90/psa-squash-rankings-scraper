"""
Test suite for exporter functionality.
"""

import pytest
from unittest.mock import patch
from pathlib import Path
from psa_squash_rankings.exporter import export_to_csv
from psa_squash_rankings.schema import ApiPlayerRecord, HtmlPlayerRecord


@pytest.fixture
def sample_api_data() -> list[ApiPlayerRecord]:
    """Create sample API data for testing."""
    return [
        {
            "rank": 1,
            "player": "Ali Farag",
            "id": 12345,
            "tournaments": 12,
            "points": 20000,
            "birthdate": "1992-01-01",
            "height_cm": 180,
            "weight_kg": 75,
            "country": "Egypt",
            "source": "api",
        },
        {
            "rank": 2,
            "player": "Paul Coll",
            "id": 67890,
            "tournaments": 10,
            "points": 18000,
            "birthdate": "1992-06-14",
            "height_cm": 185,
            "weight_kg": 80,
            "country": "New Zealand",
            "source": "api",
        },
        {
            "rank": 3,
            "player": "Diego Elias",
            "id": 11111,
            "tournaments": 11,
            "points": 17000,
            "birthdate": "1993-03-15",
            "height_cm": 175,
            "weight_kg": 70,
            "country": "Peru",
            "source": "api",
        },
    ]


@pytest.fixture
def sample_html_data() -> list[HtmlPlayerRecord]:
    """Create sample HTML data for testing."""
    return [
        {
            "rank": 1,
            "player": "Ali Farag",
            "tournaments": 12,
            "points": 20000,
            "source": "html",
        },
        {
            "rank": 2,
            "player": "Paul Coll",
            "tournaments": 10,
            "points": 18000,
            "source": "html",
        },
    ]


def test_export_to_csv_creates_file_api_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sample_api_data: list[ApiPlayerRecord],
) -> None:
    """Test that export_to_csv creates a CSV file with API data."""
    monkeypatch.setattr("psa_squash_rankings.exporter.OUTPUT_DIR", tmp_path)

    filename = "test_rankings.csv"
    export_to_csv(sample_api_data, filename)

    output_file = tmp_path / filename
    assert output_file.exists()


def test_export_to_csv_creates_file_html_data(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sample_html_data: list[HtmlPlayerRecord],
) -> None:
    """Test that export_to_csv creates a CSV file with HTML data."""
    monkeypatch.setattr("psa_squash_rankings.exporter.OUTPUT_DIR", tmp_path)

    filename = "test_rankings_fallback.csv"
    export_to_csv(sample_html_data, filename)

    output_file = tmp_path / filename
    assert output_file.exists()


def test_export_to_csv_correct_content_api(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sample_api_data: list[ApiPlayerRecord],
) -> None:
    """Test that exported CSV has correct API content."""
    import pandas as pd

    monkeypatch.setattr("psa_squash_rankings.exporter.OUTPUT_DIR", tmp_path)

    filename = "test_rankings.csv"
    export_to_csv(sample_api_data, filename)

    output_file = tmp_path / filename
    df_read = pd.read_csv(output_file)

    assert len(df_read) == 3
    assert df_read.iloc[0]["player"] == "Ali Farag"
    assert df_read.iloc[0]["id"] == 12345
    assert df_read.iloc[0]["source"] == "api"
    assert df_read.iloc[1]["player"] == "Paul Coll"
    assert df_read.iloc[2]["player"] == "Diego Elias"


def test_export_to_csv_correct_content_html(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sample_html_data: list[HtmlPlayerRecord],
) -> None:
    """Test that exported CSV has correct HTML content."""
    import pandas as pd

    monkeypatch.setattr("psa_squash_rankings.exporter.OUTPUT_DIR", tmp_path)

    filename = "test_rankings_fallback.csv"
    export_to_csv(sample_html_data, filename)

    output_file = tmp_path / filename
    df_read = pd.read_csv(output_file)

    assert len(df_read) == 2
    assert df_read.iloc[0]["player"] == "Ali Farag"
    assert df_read.iloc[0]["source"] == "html"
    assert "id" not in df_read.columns
    assert df_read.iloc[1]["player"] == "Paul Coll"


def test_export_to_csv_empty_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test exporting empty data."""
    monkeypatch.setattr("psa_squash_rankings.exporter.OUTPUT_DIR", tmp_path)

    filename = "test_rankings.csv"
    export_to_csv([], filename)


def test_export_to_csv_overwrites_existing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sample_api_data: list[ApiPlayerRecord],
) -> None:
    """Test that exporting overwrites existing file."""
    import pandas as pd

    monkeypatch.setattr("psa_squash_rankings.exporter.OUTPUT_DIR", tmp_path)

    filename = "test_rankings.csv"

    export_to_csv(sample_api_data, filename)

    new_data: list[ApiPlayerRecord] = [
        {
            "rank": 67,
            "player": "test_player",
            "id": 99999,
            "tournaments": 5,
            "points": 999999,
            "height_cm": None,
            "weight_kg": None,
            "birthdate": None,
            "country": None,
            "source": "api",
        }
    ]

    export_to_csv(new_data, filename)

    output_file = tmp_path / filename
    df_read = pd.read_csv(output_file)

    assert len(df_read) == 1
    assert df_read.iloc[0]["player"] == "test_player"
    assert df_read.iloc[0]["rank"] == 67
    assert df_read.iloc[0]["points"] == 999999


def test_export_to_csv_different_filenames(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sample_api_data: list[ApiPlayerRecord],
) -> None:
    """Test exporting to multiple different files."""
    monkeypatch.setattr("psa_squash_rankings.exporter.OUTPUT_DIR", tmp_path)

    export_to_csv(sample_api_data, "male_rankings.csv")
    export_to_csv(sample_api_data, "female_rankings.csv")
    export_to_csv(sample_api_data, "backup_rankings.csv")

    assert (tmp_path / "male_rankings.csv").exists()
    assert (tmp_path / "female_rankings.csv").exists()
    assert (tmp_path / "backup_rankings.csv").exists()


def test_export_to_csv_large_dataset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test exporting a large dataset."""
    import pandas as pd

    monkeypatch.setattr("psa_squash_rankings.exporter.OUTPUT_DIR", tmp_path)

    large_data: list[ApiPlayerRecord] = [
        {
            "rank": i,
            "player": f"Player {i}",
            "id": i,
            "tournaments": 10,
            "points": 10000 - i,
            "height_cm": None,
            "weight_kg": None,
            "birthdate": None,
            "country": None,
            "source": "api",
        }
        for i in range(1, 1001)
    ]

    filename = "large_rankings.csv"
    export_to_csv(large_data, filename)

    output_file = tmp_path / filename
    assert output_file.exists()

    df_read = pd.read_csv(output_file)
    assert len(df_read) == 1000


def test_export_to_csv_logs_success_api(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sample_api_data: list[ApiPlayerRecord],
) -> None:
    """Test that successful export of API data logs appropriate message."""
    monkeypatch.setattr("psa_squash_rankings.exporter.OUTPUT_DIR", tmp_path)

    with patch("psa_squash_rankings.exporter.get_logger") as mock_get_logger:
        mock_logger = mock_get_logger.return_value

        filename = "test_rankings.csv"
        export_to_csv(sample_api_data, filename)

        assert mock_logger.info.call_count >= 1

        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("complete API records" in call for call in info_calls)


def test_export_to_csv_logs_warning_html(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    sample_html_data: list[HtmlPlayerRecord],
) -> None:
    """Test that export of HTML data logs warning about degraded data."""
    monkeypatch.setattr("psa_squash_rankings.exporter.OUTPUT_DIR", tmp_path)

    with patch("psa_squash_rankings.exporter.get_logger") as mock_get_logger:
        mock_logger = mock_get_logger.return_value

        filename = "test_rankings_fallback.csv"
        export_to_csv(sample_html_data, filename)

        assert mock_logger.warning.call_count >= 1

        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert any("DEGRADED" in call for call in warning_calls)
