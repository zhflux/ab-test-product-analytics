import tempfile
from pathlib import Path
from datetime import timedelta

import pandas as pd
import pytest

from pipeline.ingest import load_kaggle_dataset, parse_kaggle_time, validate_columns


def test_parse_kaggle_time():
    td = parse_kaggle_time("11:48.6")
    assert td == timedelta(minutes=11, seconds=48.6)


def test_validate_columns_raises():
    df = pd.DataFrame({"id": [1], "time": ["00:01.0"]})
    with pytest.raises(ValueError, match="Missing columns"):
        validate_columns(df, {"id", "time", "converted"}, "ab_test.csv")


def test_load_kaggle_dataset(tmp_path: Path):
    ab_path = tmp_path / "ab_test.csv"
    countries_path = tmp_path / "countries_ab.csv"
    ab_df = pd.DataFrame(
        {
            "id": [1, 2],
            "time": ["00:10.0", "00:20.0"],
            "con_treat": ["control", "treatment"],
            "page": ["old_page", "new_page"],
            "converted": [0, 1],
        }
    )
    countries_df = pd.DataFrame({"id": [1, 2], "country": ["US", "UK"]})
    ab_df.to_csv(ab_path, index=False)
    countries_df.to_csv(countries_path, index=False)

    df = load_kaggle_dataset(ab_path, countries_path)
    assert "variation" in df.columns
    assert df.loc[1, "event_type"] == "purchase"
    assert df.loc[1, "country"] == "UK"
