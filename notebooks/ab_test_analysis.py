#!/usr/bin/env python3

import argparse
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm


def load_data(database_path: Path) -> pd.DataFrame:
    with sqlite3.connect(database_path) as conn:
        df = pd.read_sql_query("SELECT * FROM raw_ab_test_events", conn)
    return df


def compute_confidence_interval(successes: int, trials: int, alpha: float = 0.05) -> tuple[float, float]:
    if trials == 0:
        return 0.0, 0.0
    p = successes / trials
    z = norm.ppf(1 - alpha / 2)
    se = np.sqrt(p * (1 - p) / trials)
    return max(0.0, p - z * se), min(1.0, p + z * se)


def compute_z_test(success_a: int, n_a: int, success_b: int, n_b: int) -> tuple[float, float]:
    pooled = (success_a + success_b) / (n_a + n_b)
    se = np.sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b))
    stat = (success_b / n_b - success_a / n_a) / se
    p_value = 2 * (1 - norm.cdf(abs(stat)))
    return stat, p_value


def summarize_by(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    grouped = (
        df.groupby(group_cols)
        .agg(
            users=("user_id", pd.Series.nunique),
            conversions=("is_purchase", "sum"),
            total_revenue=("revenue", "sum"),
        )
        .reset_index()
    )
    grouped["conversion_rate"] = (grouped["conversions"] / grouped["users"]).round(4)
    grouped["revenue_per_user"] = (grouped["total_revenue"] / grouped["users"]).round(2)
    grouped["revenue_per_conversion"] = grouped.apply(
        lambda row: round(row["total_revenue"] / row["conversions"], 2) if row["conversions"] else 0.0,
        axis=1,
    )
    return grouped


def analyze(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    df["is_purchase"] = df["event_type"] == "purchase"
    df["variation"] = df["variation"].astype(str)
    df["page"] = df.get("page", "unknown").astype(str)
    df["country"] = df.get("country", "unknown").astype(str)

    variation_summary = summarize_by(df, ["variation"])
    page_summary = summarize_by(df, ["variation", "page"])
    country_summary = summarize_by(df, ["variation", "country"])

    control_rate = variation_summary.loc[variation_summary["variation"] == "control", "conversion_rate"]
    control_rate = float(control_rate.iloc[0]) if not control_rate.empty else variation_summary["conversion_rate"].min()
    variation_summary["absolute_lift"] = (variation_summary["conversion_rate"] - control_rate).round(4)
    variation_summary["relative_lift"] = (
        (variation_summary["absolute_lift"] / control_rate * 100).round(1)
        .fillna(0.0)
    )

    stats = {}
    if len(variation_summary) == 2:
        a = variation_summary.iloc[0]
        b = variation_summary.iloc[1]
        stats["z_statistic"], stats["p_value"] = compute_z_test(int(a["conversions"]), int(a["users"]), int(b["conversions"]), int(b["users"]))
        stats["control_rate_ci"] = compute_confidence_interval(int(a["conversions"]), int(a["users"]))
        stats["treatment_rate_ci"] = compute_confidence_interval(int(b["conversions"]), int(b["users"]))
    else:
        stats["z_statistic"] = np.nan
        stats["p_value"] = np.nan
        stats["control_rate_ci"] = (0.0, 0.0)
        stats["treatment_rate_ci"] = (0.0, 0.0)

    print("=== A/B Test Summary ===")
    print(variation_summary.to_string(index=False))
    print()
    print("=== Statistical Test ===")
    print(f"Z-statistic: {stats['z_statistic']:.4f}")
    print(f"P-value: {stats['p_value']:.4f}")
    print(f"Control 95% CI: {stats['control_rate_ci']}")
    print(f"Treatment 95% CI: {stats['treatment_rate_ci']}")
    print("Interpretation: низкий p-value показывает статистически значимую разницу в конверсиях.")

    return {
        "variation_summary": variation_summary,
        "page_summary": page_summary,
        "country_summary": country_summary,
        "stats": stats,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze A/B test results from the ingested dataset.")
    parser.add_argument("--database", default="data/ab_test.db", help="SQLite database file path.")
    parser.add_argument("--output-dir", default="data", help="Directory where summary CSV files are saved.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    database_path = Path(args.database)
    if not database_path.exists():
        raise FileNotFoundError(f"Database not found: {database_path}")

    df = load_data(database_path)
    results = analyze(df)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results["variation_summary"].to_csv(output_dir / "ab_test_analysis_summary.csv", index=False)
    results["page_summary"].to_csv(output_dir / "ab_test_analysis_by_page.csv", index=False)
    results["country_summary"].to_csv(output_dir / "ab_test_analysis_by_country.csv", index=False)
    print(f"Saved summary files to {output_dir}")


if __name__ == "__main__":
    main()
