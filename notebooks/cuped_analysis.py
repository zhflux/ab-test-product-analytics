"""
CUPED (Controlled-Experiment Using Pre-Experiment Data) analysis.
Uses historical user behavior to increase statistical power.
"""
import logging
from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


def calculate_cuped_adjusted_metrics(
    treatment_df: pd.DataFrame,
    control_df: pd.DataFrame,
    metric_col: str,
    covariate_col: str,
    theta: float = 1.0,
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Calculate CUPED-adjusted metric for treatment and control groups.
    
    CUPED reduces variance by using historical (pre-experiment) values as covariates.
    The adjustment factor theta balances bias-variance tradeoff.
    
    Args:
        treatment_df: DataFrame with treatment group data
        control_df: DataFrame with control group data
        metric_col: Column name for metric to analyze
        covariate_col: Column name for pre-experiment covariate
        theta: Adjustment factor (0-1), typically estimated from historical data
        
    Returns:
        treatment_adjusted: Adjusted treatment mean
        control_adjusted: Adjusted control mean
        stats_dict: Dictionary with detailed statistics
    """
    
    treatment_metric = treatment_df[metric_col].values
    treatment_covariate = treatment_df[covariate_col].values
    
    control_metric = control_df[metric_col].values
    control_covariate = control_df[covariate_col].values
    
    # Calculate means
    treatment_mean = np.mean(treatment_metric)
    control_mean = np.mean(control_metric)
    
    # Calculate pooled covariate means
    pooled_covariate_mean = np.mean(np.concatenate([treatment_covariate, control_covariate]))
    
    # CUPED adjustment: Y_adj = Y - theta * (X - X_bar)
    treatment_adjusted = treatment_metric - theta * (treatment_covariate - pooled_covariate_mean)
    control_adjusted = control_metric - theta * (control_covariate - pooled_covariate_mean)
    
    treatment_adjusted_mean = np.mean(treatment_adjusted)
    control_adjusted_mean = np.mean(control_adjusted)
    
    # Calculate variances (adjusted ones have lower variance due to covariate control)
    treatment_var_adjusted = np.var(treatment_adjusted, ddof=1)
    control_var_adjusted = np.var(control_adjusted, ddof=1)
    
    treatment_var_orig = np.var(treatment_metric, ddof=1)
    control_var_orig = np.var(control_metric, ddof=1)
    
    # Perform t-test on adjusted metrics
    n_treatment = len(treatment_adjusted)
    n_control = len(control_adjusted)
    
    se_adjusted = np.sqrt(treatment_var_adjusted / n_treatment + control_var_adjusted / n_control)
    se_orig = np.sqrt(treatment_var_orig / n_treatment + control_var_orig / n_control)
    
    if se_adjusted > 0:
        t_stat = (treatment_adjusted_mean - control_adjusted_mean) / se_adjusted
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n_treatment + n_control - 2))
    else:
        t_stat = np.nan
        p_value = 1.0
    
    # Calculate relative lift
    relative_lift = (treatment_adjusted_mean - control_adjusted_mean) / abs(control_adjusted_mean) * 100 if control_adjusted_mean != 0 else 0
    
    # Variance reduction
    variance_reduction_pct = (1 - (treatment_var_adjusted + control_var_adjusted) / (treatment_var_orig + control_var_orig)) * 100
    
    stats_dict = {
        "treatment_mean_original": treatment_mean,
        "control_mean_original": control_mean,
        "treatment_mean_adjusted": treatment_adjusted_mean,
        "control_mean_adjusted": control_adjusted_mean,
        "treatment_variance_original": treatment_var_orig,
        "control_variance_original": control_var_orig,
        "treatment_variance_adjusted": treatment_var_adjusted,
        "control_variance_adjusted": control_var_adjusted,
        "standard_error_original": se_orig,
        "standard_error_adjusted": se_adjusted,
        "t_statistic": t_stat,
        "p_value": p_value,
        "relative_lift_pct": relative_lift,
        "variance_reduction_pct": variance_reduction_pct,
        "n_treatment": n_treatment,
        "n_control": n_control,
        "is_significant": p_value < 0.05,
    }
    
    logger.info(
        f"CUPED Analysis: "
        f"Lift={relative_lift:.2f}%, "
        f"Variance reduction={variance_reduction_pct:.1f}%, "
        f"p-value={p_value:.4f}"
    )
    
    return treatment_adjusted_mean, control_adjusted_mean, stats_dict


def estimate_theta(
    historical_df: pd.DataFrame,
    metric_col: str,
    covariate_col: str,
) -> float:
    """
    Estimate optimal theta from historical data using correlation.
    
    theta = correlation^2 between metric and covariate
    This represents the fraction of variance explained by the covariate.
    
    Args:
        historical_df: DataFrame with historical data
        metric_col: Column name for metric
        covariate_col: Column name for covariate
        
    Returns:
        Estimated theta value (0-1)
    """
    metric = historical_df[metric_col].dropna()
    covariate = historical_df[covariate_col].dropna()
    
    # Use common indices to ensure alignment
    common_idx = metric.index.intersection(covariate.index)
    metric = metric[common_idx]
    covariate = covariate[common_idx]
    
    if len(metric) < 2:
        logger.warning("Insufficient data for theta estimation, using theta=0.5")
        return 0.5
    
    correlation = metric.corr(covariate)
    theta = correlation ** 2
    theta = max(0, min(1, theta))  # Ensure 0 <= theta <= 1
    
    logger.info(f"Estimated theta={theta:.4f} from correlation={correlation:.4f}")
    
    return theta


def cuped_summary(results: Dict[str, Any], metric_name: str = "Metric") -> pd.DataFrame:
    """
    Create a summary DataFrame of CUPED results.
    
    Args:
        results: Dictionary from calculate_cuped_adjusted_metrics
        metric_name: Name of the metric being analyzed
        
    Returns:
        Summary DataFrame
    """
    summary = pd.DataFrame({
        "Metric": [metric_name],
        "Treatment (Original)": [results["treatment_mean_original"]],
        "Control (Original)": [results["control_mean_original"]],
        "Treatment (Adjusted)": [results["treatment_mean_adjusted"]],
        "Control (Adjusted)": [results["control_mean_adjusted"]],
        "Lift %": [results["relative_lift_pct"]],
        "P-Value": [results["p_value"]],
        "Significant": [results["is_significant"]],
        "Variance Reduction %": [results["variance_reduction_pct"]],
    })
    
    return summary
