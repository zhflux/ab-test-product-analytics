#!/usr/bin/env python3

import argparse
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

sns.set_theme(style="whitegrid")


def load_data(database_path: Path) -> pd.DataFrame:
    with sqlite3.connect(database_path) as conn:
        df = pd.read_sql_query("SELECT * FROM raw_ab_test_events", conn)
    return df


def data_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    quality = [
        {"metric": "row_count", "value": len(df)},
        {"metric": "column_count", "value": len(df.columns)},
        {"metric": "duplicated_event_id", "value": int(df["event_id"].duplicated().sum())},
        {"metric": "duplicate_user_rows", "value": int(df.duplicated(subset=["user_id", "event_date", "event_type"]).sum())},
    ]

    for column in ["user_id", "variation", "event_type", "country", "page", "event_date"]:
        if column in df.columns:
            quality.append({"metric": f"missing_{column}", "value": int(df[column].isna().sum())})

    return pd.DataFrame(quality)


def plot_distribution(df: pd.DataFrame, column: str, output_path: Path) -> None:
    plt.figure(figsize=(10, 5))
    order = df[column].value_counts().index
    sns.countplot(data=df, x=column, order=order)
    plt.title(f"Distribution of {column}")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def plot_conversion_by_segment(df: pd.DataFrame, group_column: str, output_path: Path) -> None:
    summary = (
        df.assign(is_purchase=df["event_type"] == "purchase")
        .groupby(["variation", group_column])
        .agg(users=("user_id", pd.Series.nunique), purchases=("is_purchase", "sum"))
        .reset_index()
    )
    summary["conversion_rate"] = summary["purchases"] / summary["users"]

    plt.figure(figsize=(12, 6))
    sns.barplot(data=summary, x=group_column, y="conversion_rate", hue="variation")
    plt.title(f"Conversion rate by {group_column} and variation")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run exploratory data analysis for the AB test dataset.")
    parser.add_argument("--database", default="data/ab_test.db", help="SQLite database path.")
    parser.add_argument("--output-dir", default="reports", help="Directory for charts and quality report.")
    args = parser.parse_args()

    database_path = Path(args.database)
    if not database_path.exists():
        raise FileNotFoundError(f"Database not found: {database_path}")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = load_data(database_path)
    quality_report = data_quality_report(df)
    quality_report.to_csv(output_dir / "ab_test_data_quality.csv", index=False)

    plot_distribution(df, "variation", output_dir / "variation_distribution.png")
    plot_distribution(df, "page", output_dir / "page_distribution.png")
    plot_distribution(df, "country", output_dir / "country_distribution.png")
    plot_conversion_by_segment(df, "page", output_dir / "conversion_by_page.png")
    plot_conversion_by_segment(df, "country", output_dir / "conversion_by_country.png")

    print(f"Saved EDA outputs to {output_dir}")


if __name__ == "__main__":
    main()
