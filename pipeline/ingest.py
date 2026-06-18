#!/usr/bin/env python3
"""
Data ingestion pipeline for A/B test experiments.
Supports synthetic data generation and Kaggle dataset loading.
"""

import argparse
import logging
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple, Set

import numpy as np
import pandas as pd

from pipeline.config import setup_logging
from pipeline.data_validation import run_data_quality_checks, print_validation_report

logger = setup_logging(__name__)


KAGGLE_AB_COLUMNS: Set[str] = {"id", "time", "con_treat", "page", "converted"}
KAGGLE_COUNTRIES_COLUMNS: Set[str] = {"id", "country"}


def parse_kaggle_time(value: str) -> timedelta:
    """Parse Kaggle time format (mm:ss) to timedelta."""
    if pd.isna(value):
        return timedelta(0)
    value = str(value).strip()
    if ":" not in value:
        return timedelta(0)
    minutes, seconds = value.split(":", 1)
    return timedelta(minutes=int(minutes), seconds=float(seconds))


def validate_columns(df: pd.DataFrame, expected_columns: Set[str], source_name: str) -> None:
    """Validate that DataFrame contains all expected columns."""
    missing = expected_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {source_name}: {sorted(missing)}")


def generate_ab_test_data(num_users: int = 5000, num_days: int = 30, seed: int = 2026) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    experiment_name = "checkout_redesign"
    start_date = datetime(2026, 1, 1)
    users = [f"user_{i:05d}" for i in range(1, num_users + 1)]
    variation = rng.choice(["control", "treatment"], size=num_users, p=[0.5, 0.5])
    assigned_days = rng.integers(0, num_days, size=num_users)
    assigned_at = [start_date + timedelta(days=int(d)) for d in assigned_days]
    countries = rng.choice(["US", "CA", "UK", "DE", "FR", "BR", "IN"], size=num_users, p=[0.35, 0.1, 0.15, 0.1, 0.1, 0.1, 0.1])
    conversion_probs = np.where(variation == "control", 0.08, 0.12)
    converted = rng.random(num_users) < conversion_probs
    revenue = np.where(converted, np.round(rng.normal(loc=82, scale=22, size=num_users).clip(10, 220), 2), 0.0)

    rows = []
    event_id = 1

    for idx, user_id in enumerate(users):
        session_id = f"session_{idx + 1:06d}"
        event_time = assigned_at[idx]
        country = countries[idx]
        group = variation[idx]
        page = "old_page" if group == "control" else "new_page"
        conversion = converted[idx]
        revenue_amount = float(revenue[idx])

        rows.append(
            {
                "event_id": event_id,
                "user_id": user_id,
                "experiment_name": experiment_name,
                "variation": group,
                "event_date": event_time.strftime("%Y-%m-%d %H:%M:%S"),
                "event_type": "session_start",
                "revenue": 0.0,
                "session_id": session_id,
                "country": country,
                "page": page,
            }
        )
        event_id += 1

        rows.append(
            {
                "event_id": event_id,
                "user_id": user_id,
                "experiment_name": experiment_name,
                "variation": group,
                "event_date": (event_time + timedelta(minutes=8)).strftime("%Y-%m-%d %H:%M:%S"),
                "event_type": "page_view",
                "revenue": 0.0,
                "session_id": session_id,
                "country": country,
                "page": page,
            }
        )
        event_id += 1

        if conversion:
            rows.append(
                {
                    "event_id": event_id,
                    "user_id": user_id,
                    "experiment_name": experiment_name,
                    "variation": group,
                    "event_date": (event_time + timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S"),
                    "event_type": "purchase",
                    "revenue": revenue_amount,
                    "session_id": session_id,
                    "country": country,
                    "page": page,
                }
            )
        else:
            event_type = "signup" if rng.random() < 0.14 else "page_view"
            rows.append(
                {
                    "event_id": event_id,
                    "user_id": user_id,
                    "experiment_name": experiment_name,
                    "variation": group,
                    "event_date": (event_time + timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S"),
                    "event_type": event_type,
                    "revenue": 0.0,
                    "session_id": session_id,
                    "country": country,
                    "page": page,
                }
            )
        event_id += 1

    df = pd.DataFrame(rows)
    df = df.sort_values(["event_date", "event_id"]).reset_index(drop=True)
    df["revenue"] = df["revenue"].astype(float)
    return df


def load_kaggle_dataset(ab_path: Path, countries_path: Path | None = None) -> pd.DataFrame:
    ab = pd.read_csv(ab_path)
    validate_columns(ab, KAGGLE_AB_COLUMNS, "ab_test.csv")

    if countries_path is not None:
        countries = pd.read_csv(countries_path)
        validate_columns(countries, KAGGLE_COUNTRIES_COLUMNS, "countries_ab.csv")
        ab = ab.drop_duplicates(subset=["id"])
        df = ab.merge(countries, on="id", how="left")
    else:
        df = ab.copy()
        df["country"] = "unknown"

    df["country"] = df["country"].fillna("unknown")
    df["converted"] = df["converted"].fillna(0).astype(int)
    df["variation"] = df["con_treat"].astype(str)
    df["user_id"] = df["id"].astype(str)
    df["experiment_name"] = "kaggle_ab_test"
    df["page"] = df["page"].astype(str).fillna("unknown")
    df["event_type"] = np.where(df["converted"] == 1, "purchase", "page_view")
    base_date = datetime(2021, 1, 1)
    df["event_date"] = (
        df["time"].apply(parse_kaggle_time)
        .apply(lambda td: base_date + td)
        .dt.strftime("%Y-%m-%d %H:%M:%S")
    )
    df["revenue"] = df["converted"].astype(float)
    df["session_id"] = "session_" + df["user_id"].str.zfill(6)

    column_order = [
        "event_id",
        "user_id",
        "experiment_name",
        "variation",
        "event_date",
        "event_type",
        "revenue",
        "session_id",
        "country",
        "page",
    ]

    df["event_id"] = np.arange(1, len(df) + 1)
    return df[column_order + [col for col in df.columns if col not in column_order]]


def write_csv(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, index=False)


def write_sqlite(df: pd.DataFrame, path: Path) -> None:
    with sqlite3.connect(path) as conn:
        df.to_sql("raw_ab_test_events", conn, if_exists="replace", index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and ingest A/B test experiment data.")
    parser.add_argument("--output-dir", default="data", help="Directory where generated files are saved.")
    parser.add_argument("--num-users", type=int, default=5000, help="Number of unique users to generate.")
    parser.add_argument("--num-days", type=int, default=30, help="Number of experiment days to simulate.")
    parser.add_argument("--seed", type=int, default=2026, help="Random seed for reproducible data.")
    parser.add_argument("--input-csv", default=None, help="Optional raw CSV file to ingest instead of generating synthetic data.")
    parser.add_argument("--kaggle-ab", default=None, help="Path to Kaggle ab_test.csv file.")
    parser.add_argument("--kaggle-countries", default=None, help="Path to Kaggle countries_ab.csv file.")
    return parser.parse_args()


def main() -> None:
    """Main ingestion pipeline."""
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting ingestion pipeline. Output directory: {output_dir}")

    if args.kaggle_ab:
        kaggle_path = Path(args.kaggle_ab)
        if not kaggle_path.exists():
            logger.error(f"Kaggle ab_test.csv not found: {kaggle_path}")
            raise FileNotFoundError(f"Kaggle ab_test.csv not found: {kaggle_path}")
        countries_path = Path(args.kaggle_countries) if args.kaggle_countries else None
        if countries_path is not None and not countries_path.exists():
            logger.error(f"Kaggle countries_ab.csv not found: {countries_path}")
            raise FileNotFoundError(f"Kaggle countries_ab.csv not found: {countries_path}")
        logger.info("Loading Kaggle dataset...")
        df = load_kaggle_dataset(kaggle_path, countries_path)
    elif args.input_csv:
        raw_path = Path(args.input_csv)
        if not raw_path.exists():
            logger.error(f"Input CSV not found: {raw_path}")
            raise FileNotFoundError(f"Input CSV not found: {raw_path}")
        logger.info(f"Loading CSV from {raw_path}...")
        df = pd.read_csv(raw_path)
    else:
        logger.info(f"Generating synthetic data: {args.num_users} users, {args.num_days} days, seed={args.seed}")
        df = generate_ab_test_data(num_users=args.num_users, num_days=args.num_days, seed=args.seed)

    # Rename columns to standard format
    df = df.rename(columns={'event_date': 'timestamp'})
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    logger.info(f"Loaded {len(df)} events for {df['user_id'].nunique()} users")

    # Run data validation
    logger.info("Running data quality checks...")
    validation_results = run_data_quality_checks(df)
    print_validation_report(validation_results)

    # Write outputs
    csv_path = output_dir / "raw_ab_test_events.csv"
    db_path = output_dir / "ab_test.db"

    logger.info(f"Writing CSV to {csv_path}")
    write_csv(df, csv_path)
    
    logger.info(f"Writing SQLite database to {db_path}")
    write_sqlite(df, db_path)

    # Summary statistics
    summary = (
        df.groupby("variation")
        .agg(users=("user_id", pd.Series.nunique),
             conversions=("event_type", lambda values: (values == "purchase").sum()),
             total_revenue=("revenue", "sum"))
        .reset_index()
    )
    summary["conversion_rate"] = (summary["conversions"] / summary["users"]).round(4)

    generated_users = df["user_id"].nunique()
    logger.info(f"Successfully ingested {len(df)} event rows for {generated_users} users")
    print(f"\nSummary by variation:")
    print(summary.to_string(index=False))
    print(f"\n✓ Saved CSV to {csv_path}")
    print(f"✓ Saved SQLite database to {db_path}")


if __name__ == "__main__":
    main()
