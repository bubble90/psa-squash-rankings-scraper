"""
Test suite for exporter functionality.
"""

import pytest
import pandas as pd
from unittest.mock import patch
from exporter import export_to_csv


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "rank": [1, 2, 3],
            "player": ["Ali Farag", "Paul Coll", "Diego Elias"],
            "id": [12345, 67890, 11111],
            "tournaments": [12, 10, 11],
            "points": [20000, 18000, 17000],
            "birthdate": ["1992-01-01", "1992-06-14", "1993-03-15"],
            "height(cm)": [180, 185, 175],
            "weight(kg)": [75, 80, 70],
            "country": ["Egypt", "New Zealand", "Peru"],
        }
    )


@pytest.fixture
def empty_dataframe():
    """Create an empty DataFrame with columns but no rows."""
    return pd.DataFrame(columns=["rank", "player", "points"])


def test_export_to_csv_creates_file(tmp_path, monkeypatch, sample_dataframe):
    """Test that export_to_csv creates a CSV file."""

    monkeypatch.setattr("exporter.OUTPUT_DIR", tmp_path)

    filename = "test_rankings.csv"
    export_to_csv(sample_dataframe, filename)

    output_file = tmp_path / filename
    assert output_file.exists()


def test_export_to_csv_correct_content(tmp_path, monkeypatch, sample_dataframe):
    """Test that exported CSV has correct content."""
    monkeypatch.setattr("exporter.OUTPUT_DIR", tmp_path)

    filename = "test_rankings.csv"
    export_to_csv(sample_dataframe, filename)

    output_file = tmp_path / filename
    df_read = pd.read_csv(output_file)

    assert len(df_read) == 3
    assert list(df_read.columns) == list(sample_dataframe.columns)
    assert df_read.iloc[0]["player"] == "Ali Farag"
    assert df_read.iloc[1]["player"] == "Paul Coll"
    assert df_read.iloc[2]["player"] == "Diego Elias"


def test_export_to_csv_empty_dataframe(tmp_path, monkeypatch, empty_dataframe):
    """Test exporting an empty DataFrame."""
    monkeypatch.setattr("exporter.OUTPUT_DIR", tmp_path)

    filename = "test_rankings.csv"
    export_to_csv(empty_dataframe, filename)

    output_file = tmp_path / filename
    df_read = pd.read_csv(output_file)

    assert len(df_read) == 0
    assert list(df_read.columns) == ["rank", "player", "points"]


def test_export_to_csv_overwrites_existing(tmp_path, monkeypatch, sample_dataframe):
    """Test that exporting overwrites existing file."""
    monkeypatch.setattr("exporter.OUTPUT_DIR", tmp_path)

    filename = "test_rankings.csv"

    export_to_csv(sample_dataframe, filename)

    new_df = pd.DataFrame(
        {
            "player": ["test_player"],
            "rank": [67],
            "points": [999999],
        }
    )

    export_to_csv(new_df, filename)

    output_file = tmp_path / filename
    df_read = pd.read_csv(output_file)

    assert df_read.iloc[0]["player"] == "test_player"
    assert df_read.iloc[0]["rank"] == 67
    assert df_read.iloc[0]["points"] == 999999


def test_export_to_csv_different_filenames(tmp_path, monkeypatch, sample_dataframe):
    """Test exporting to multiple different files."""
    monkeypatch.setattr("exporter.OUTPUT_DIR", tmp_path)

    export_to_csv(sample_dataframe, "male_rankings.csv")
    export_to_csv(sample_dataframe, "female_rankings.csv")
    export_to_csv(sample_dataframe, "backup_rankings.csv")

    assert (tmp_path / "male_rankings.csv").exists()
    assert (tmp_path / "female_rankings.csv").exists()
    assert (tmp_path / "backup_rankings.csv").exists()


def test_export_to_csv_large_dataset(tmp_path, monkeypatch):
    """Test exporting a large DataFrame."""
    monkeypatch.setattr("exporter.OUTPUT_DIR", tmp_path)

    large_df = pd.DataFrame(
        {
            "rank": range(1, 1001),
            "player": [f"Player {i}" for i in range(1, 1001)],
            "points": [10000 - i for i in range(1, 1001)],
        }
    )

    filename = "large_rankings.csv"
    export_to_csv(large_df, filename)

    output_file = tmp_path / filename
    assert output_file.exists()

    df_read = pd.read_csv(output_file)
    assert len(df_read) == 1000


def test_export_to_csv_logs_success(tmp_path, monkeypatch, sample_dataframe):
    """Test that successful export logs appropriate message."""
    monkeypatch.setattr("exporter.OUTPUT_DIR", tmp_path)

    with patch("exporter.logger") as mock_logger:
        filename = "test_rankings.csv"
        export_to_csv(sample_dataframe, filename)

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "Exported" in call_args
        assert "3 rows" in call_args
        assert filename in call_args
