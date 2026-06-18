"""
Streamlit dashboard for A/B test analysis.
Interactive exploration and visualization of experiment results.

Run with: streamlit run dashboard/app.py
"""
import logging
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np
import streamlit as st
import sqlite3

# Add parent directories to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.config import settings, setup_logging
from notebooks.bayesian_analysis import BayesianAnalyzer, bayesian_summary
from notebooks.cuped_analysis import calculate_cuped_adjusted_metrics, estimate_theta, cuped_summary
from notebooks.cohort_analysis import create_cohorts, cohort_retention_analysis

logger = setup_logging(__name__)


@st.cache_resource
def load_database() -> sqlite3.Connection:
    """Load SQLite database."""
    return sqlite3.connect(str(settings.db_path))


@st.cache_data
def load_events_data() -> pd.DataFrame:
    """Load events data from database."""
    conn = load_database()
    query = """
    SELECT * FROM events
    """
    df = pd.read_sql_query(query, conn)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df


@st.cache_data
def load_user_data() -> pd.DataFrame:
    """Load user data."""
    conn = load_database()
    query = """
    SELECT DISTINCT user_id, variation, country FROM events
    """
    df = pd.read_sql_query(query, conn)
    return df


def main():
    """Main Streamlit application."""
    st.set_page_config(page_title="A/B Test Analytics", layout="wide")
    st.title("🧪 A/B Test Analytics Dashboard")
    
    # Load data
    try:
        events_df = load_events_data()
        user_df = load_user_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select Analysis", [
        "Overview",
        "Frequentist Analysis",
        "Bayesian Analysis",
        "CUPED Analysis",
        "Cohort Analysis",
        "Comparison",
    ])
    
    if page == "Overview":
        show_overview(events_df, user_df)
    elif page == "Frequentist Analysis":
        show_frequentist(events_df)
    elif page == "Bayesian Analysis":
        show_bayesian(events_df)
    elif page == "CUPED Analysis":
        show_cuped(events_df)
    elif page == "Cohort Analysis":
        show_cohort(events_df)
    elif page == "Comparison":
        show_comparison(events_df)


def show_overview(events_df: pd.DataFrame, user_df: pd.DataFrame):
    """Overview page with key metrics."""
    st.header("Experiment Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", user_df['user_id'].nunique())
    
    with col2:
        st.metric("Total Events", len(events_df))
    
    with col3:
        st.metric("Variations", user_df['variation'].nunique())
    
    with col4:
        st.metric("Countries", user_df['country'].nunique())
    
    st.divider()
    
    # Variation breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Users by Variation")
        variation_users = user_df['variation'].value_counts()
        st.bar_chart(variation_users)
    
    with col2:
        st.subheader("Events by Type")
        event_types = events_df['event_type'].value_counts()
        st.bar_chart(event_types)
    
    # Time series
    st.subheader("Events Over Time")
    time_series = events_df.groupby(pd.Grouper(key='timestamp', freq='D')).size()
    st.line_chart(time_series)


def show_frequentist(events_df: pd.DataFrame):
    """Frequentist statistical analysis."""
    st.header("Frequentist A/B Test Analysis")
    
    # Select metrics
    metrics = st.multiselect(
        "Select metrics to analyze",
        ["conversion_rate", "revenue_per_user", "revenue_per_conversion"],
        default=["conversion_rate"]
    )
    
    if not metrics:
        st.warning("Select at least one metric")
        return
    
    # Calculate metrics by variation
    variation_data = []
    for variation in events_df['variation'].unique():
        var_df = events_df[events_df['variation'] == variation]
        
        users = var_df['user_id'].nunique()
        conversions = (var_df['event_type'] == 'conversion').sum()
        revenue = var_df['revenue'].sum()
        
        variation_data.append({
            'Variation': variation,
            'Users': users,
            'Conversions': conversions,
            'Conversion Rate': conversions / users if users > 0 else 0,
            'Revenue': revenue,
            'Revenue per User': revenue / users if users > 0 else 0,
        })
    
    results_df = pd.DataFrame(variation_data)
    st.dataframe(results_df, use_container_width=True)
    
    # Statistical test
    if len(results_df) == 2:
        st.subheader("Statistical Significance")
        
        treatment = events_df[events_df['variation'] == results_df.iloc[0, 0]]
        control = events_df[events_df['variation'] == results_df.iloc[1, 0]]
        
        t1_users = treatment['user_id'].nunique()
        t1_conversions = (treatment['event_type'] == 'conversion').sum()
        
        t2_users = control['user_id'].nunique()
        t2_conversions = (control['event_type'] == 'conversion').sum()
        
        # Z-test
        p1 = t1_conversions / t1_users if t1_users > 0 else 0
        p2 = t2_conversions / t2_users if t2_users > 0 else 0
        
        pooled_p = (t1_conversions + t2_conversions) / (t1_users + t2_users)
        se = np.sqrt(pooled_p * (1 - pooled_p) * (1/t1_users + 1/t2_users))
        
        if se > 0:
            z_stat = (p1 - p2) / se
            from scipy import stats
            p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))
        else:
            z_stat = 0
            p_value = 1.0
        
        st.metric("Z-statistic", f"{z_stat:.4f}")
        st.metric("P-value", f"{p_value:.4f}")
        st.metric("Significant at 0.05?", "Yes ✓" if p_value < 0.05 else "No ✗")


def show_bayesian(events_df: pd.DataFrame):
    """Bayesian analysis."""
    st.header("Bayesian A/B Test Analysis")
    
    # Get variations
    variations = sorted(events_df['variation'].unique())
    
    if len(variations) < 2:
        st.warning("Need at least 2 variations for analysis")
        return
    
    col1, col2 = st.columns(2)
    with col1:
        treatment = st.selectbox("Treatment", variations)
    with col2:
        control = st.selectbox("Control", [v for v in variations if v != treatment])
    
    # Calculate conversion rates
    treatment_df = events_df[events_df['variation'] == treatment]
    control_df = events_df[events_df['variation'] == control]
    
    t_users = treatment_df['user_id'].nunique()
    t_conversions = (treatment_df['event_type'] == 'conversion').sum()
    
    c_users = control_df['user_id'].nunique()
    c_conversions = (control_df['event_type'] == 'conversion').sum()
    
    # Bayesian analysis
    analyzer = BayesianAnalyzer()
    results = analyzer.analyze_conversion(
        t_conversions, t_users,
        c_conversions, c_users,
    )
    
    # Display results
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Treatment Rate", f"{results['treatment_posterior_mean']:.4f}")
    with col2:
        st.metric("Control Rate", f"{results['control_posterior_mean']:.4f}")
    with col3:
        st.metric("Expected Lift %", f"{results['expected_lift_pct']:.2f}%")
    
    st.metric("P(Treatment > Control)", f"{results['prob_treatment_better']:.4f}")
    
    # Visualize distributions
    st.subheader("Posterior Distributions")
    
    import plotly.graph_objects as go
    fig = go.Figure()
    
    fig.add_trace(go.Histogram(
        x=results['treatment_samples'],
        name='Treatment',
        opacity=0.7,
        nbinsx=50,
    ))
    fig.add_trace(go.Histogram(
        x=results['control_samples'],
        name='Control',
        opacity=0.7,
        nbinsx=50,
    ))
    
    fig.update_layout(
        title="Posterior Distribution of Conversion Rates",
        xaxis_title="Conversion Rate",
        yaxis_title="Frequency",
        barmode='overlay',
    )
    st.plotly_chart(fig, use_container_width=True)


def show_cuped(events_df: pd.DataFrame):
    """CUPED analysis."""
    st.header("CUPED: Variance Reduction Analysis")
    
    st.info(
        "CUPED uses historical covariate data to reduce variance and increase statistical power. "
        "This example uses pre-experiment user activity as a covariate."
    )
    
    variations = sorted(events_df['variation'].unique())
    
    if len(variations) < 2:
        st.warning("Need at least 2 variations")
        return
    
    treatment_var = variations[0]
    control_var = variations[1]
    
    treatment_df = events_df[events_df['variation'] == treatment_var].copy()
    control_df = events_df[events_df['variation'] == control_var].copy()
    
    # Simulate pre-experiment covariate
    treatment_df['pre_revenue'] = np.random.exponential(10, len(treatment_df))
    control_df['pre_revenue'] = np.random.exponential(10, len(control_df))
    
    # Estimate theta
    combined_df = pd.concat([treatment_df, control_df])
    theta = estimate_theta(combined_df, 'revenue', 'pre_revenue')
    
    st.metric("Estimated Theta (Variance Control)", f"{theta:.4f}")
    
    # CUPED adjustment
    t_adjusted, c_adjusted, stats_dict = calculate_cuped_adjusted_metrics(
        treatment_df, control_df,
        'revenue', 'pre_revenue',
        theta=theta
    )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Lift %", f"{stats_dict['relative_lift_pct']:.2f}%")
    with col2:
        st.metric("Variance Reduction %", f"{stats_dict['variance_reduction_pct']:.1f}%")
    with col3:
        st.metric("P-value", f"{stats_dict['p_value']:.4f}")


def show_cohort(events_df: pd.DataFrame):
    """Cohort analysis."""
    st.header("Cohort Retention Analysis")
    
    # Create cohorts
    cohort_df = create_cohorts(
        events_df,
        user_col='user_id',
        timestamp_col='timestamp',
        cohort_window_days=7,
    )
    
    # Cohort retention
    cohort_results = cohort_retention_analysis(
        cohort_df,
        user_col='user_id',
        value_col='revenue',
    )
    
    st.subheader("Retention by Cohort")
    st.dataframe(cohort_results['retention'], use_container_width=True)
    
    st.subheader("Revenue by Cohort")
    st.dataframe(cohort_results['value'], use_container_width=True)
    
    st.subheader("Cumulative Value")
    st.dataframe(cohort_results['cumulative_value'], use_container_width=True)


def show_comparison(events_df: pd.DataFrame):
    """Side-by-side comparison."""
    st.header("Variation Comparison")
    
    variations = sorted(events_df['variation'].unique())
    
    comparison_data = []
    for var in variations:
        var_df = events_df[events_df['variation'] == var]
        
        users = var_df['user_id'].nunique()
        conversions = (var_df['event_type'] == 'conversion').sum()
        revenue = var_df['revenue'].sum()
        avg_order_value = var_df[var_df['event_type'] == 'purchase']['revenue'].mean()
        
        comparison_data.append({
            'Variation': var,
            'Users': users,
            'Conversions': conversions,
            'Conv Rate %': (conversions/users*100) if users > 0 else 0,
            'Revenue': f"${revenue:,.2f}",
            'Rev/User': f"${revenue/users:.2f}" if users > 0 else "$0",
            'AOV': f"${avg_order_value:.2f}" if not np.isnan(avg_order_value) else "N/A",
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)


if __name__ == "__main__":
    main()
