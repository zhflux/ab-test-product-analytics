"""
Cohort analysis for A/B testing.
Tracks user behavior across time periods after experiment start.
"""
import logging
from typing import Dict, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def create_cohorts(
    df: pd.DataFrame,
    user_col: str,
    timestamp_col: str,
    cohort_window_days: int = 7,
) -> pd.DataFrame:
    """
    Create cohort groups based on first activity date.
    
    Args:
        df: DataFrame with user activity data
        user_col: Column name for user identifier
        timestamp_col: Column name for timestamp
        cohort_window_days: Days per cohort window
        
    Returns:
        DataFrame with added cohort columns
    """
    df = df.copy()
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    
    # Get first activity date per user
    user_first_activity = df.groupby(user_col)[timestamp_col].min()
    df["first_activity"] = df[user_col].map(user_first_activity)
    
    # Calculate cohort date (week/period start)
    df["cohort_date"] = df["first_activity"].dt.to_period(f"{cohort_window_days}D").dt.start_time
    
    # Calculate days since cohort start
    df["days_since_cohort"] = (df[timestamp_col] - df["first_activity"]).dt.days
    df["cohort_age"] = (df["days_since_cohort"] // cohort_window_days) * cohort_window_days
    
    logger.info(f"Created {df['cohort_date'].nunique()} cohorts")
    
    return df


def cohort_retention_analysis(
    df: pd.DataFrame,
    user_col: str,
    cohort_col: str = "cohort_date",
    age_col: str = "cohort_age",
    value_col: str = "revenue",
    variation_col: str = "variation",
) -> Dict[str, pd.DataFrame]:
    """
    Calculate cohort retention and value metrics.
    
    Args:
        df: DataFrame with cohort information
        user_col: Column name for user identifier
        cohort_col: Column name for cohort date
        age_col: Column name for cohort age
        value_col: Column name for value metric
        variation_col: Column name for variation/treatment
        
    Returns:
        Dictionary with retention and value cohort tables
    """
    df = df.copy()
    
    # Retention: Active users per cohort and age
    retention = df.groupby([cohort_col, age_col, variation_col])[user_col].nunique().reset_index()
    retention.columns = [cohort_col, age_col, variation_col, "active_users"]
    
    # Pivot to see cohort x age
    retention_pivot = retention.pivot_table(
        index=[cohort_col, variation_col],
        columns=age_col,
        values="active_users",
        fill_value=0
    )
    
    # Value: Total value per cohort and age
    value_cohort = df.groupby([cohort_col, age_col, variation_col])[value_col].agg(["sum", "mean"]).reset_index()
    value_cohort.columns = [cohort_col, age_col, variation_col, "total_value", "avg_value"]
    
    value_pivot = value_cohort.pivot_table(
        index=[cohort_col, variation_col],
        columns=age_col,
        values="total_value",
        fill_value=0
    )
    
    # Cumulative value
    cumulative_value = df.groupby([cohort_col, user_col, variation_col])[value_col].sum().reset_index()
    cumulative_by_cohort = cumulative_value.groupby([cohort_col, variation_col])[value_col].agg(["sum", "mean", "median"]).reset_index()
    
    logger.info(f"Cohort retention: {len(retention_pivot)} cohort-variation combinations")
    logger.info(f"Cohort value: {len(value_pivot)} cohort-variation combinations")
    
    return {
        "retention": retention_pivot,
        "value": value_pivot,
        "cumulative_value": cumulative_by_cohort,
        "retention_detail": retention,
        "value_detail": value_cohort,
    }


def cohort_comparison(
    cohort_data: Dict[str, pd.DataFrame],
    metric: str = "retention",
) -> pd.DataFrame:
    """
    Compare variations across cohorts for a specific metric.
    
    Args:
        cohort_data: Dictionary from cohort_retention_analysis
        metric: Metric to compare ('retention' or 'value')
        
    Returns:
        Comparison DataFrame
    """
    if metric == "retention":
        detail_df = cohort_data["retention_detail"]
        metric_col = "active_users"
    else:
        detail_df = cohort_data["value_detail"]
        metric_col = "total_value"
    
    # Calculate metrics by variation and cohort age
    comparison = detail_df.groupby(["cohort_date", "cohort_age", "variation"])[metric_col].agg(["sum", "mean"]).reset_index()
    
    # Pivot for easier comparison
    pivot = comparison.pivot_table(
        index=["cohort_date", "cohort_age"],
        columns="variation",
        values="sum",
        fill_value=0
    )
    
    if len(pivot.columns) == 2:
        pivot["lift_pct"] = ((pivot.iloc[:, 1] - pivot.iloc[:, 0]) / pivot.iloc[:, 0] * 100).replace([np.inf, -np.inf], 0)
    
    return pivot


def plot_cohort_heatmap(
    cohort_pivot: pd.DataFrame,
    title: str = "Cohort Retention Heatmap",
):
    """
    Helper to plot cohort heatmap (requires plotly).
    
    Args:
        cohort_pivot: Pivot table from cohort analysis
        title: Title for the plot
    """
    try:
        import plotly.figure_factory as ff
        
        # Normalize for heatmap
        normalized = cohort_pivot.div(cohort_pivot.iloc[:, 0], axis=0) * 100
        
        fig = ff.create_annotated_heatmap(
            z=normalized.values,
            x=normalized.columns,
            y=normalized.index,
            colorscale="RdYlGn",
            showscale=True,
        )
        fig.update_layout(title=title)
        return fig
    except ImportError:
        logger.warning("Plotly not available for cohort visualization")
        return None
