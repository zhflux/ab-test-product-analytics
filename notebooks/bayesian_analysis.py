"""
Bayesian A/B testing analysis.
Alternative to frequentist approach with probabilistic interpretation.
"""
import logging
from typing import Dict, Tuple, Any
import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class BayesianAnalyzer:
    """Bayesian A/B test analyzer using Beta-Binomial conjugate prior."""
    
    def __init__(self, alpha_prior: float = 1.0, beta_prior: float = 1.0):
        """
        Initialize Bayesian analyzer.
        
        Args:
            alpha_prior: Alpha parameter of Beta prior (default: 1, uniform)
            beta_prior: Beta parameter of Beta prior (default: 1, uniform)
        """
        self.alpha_prior = alpha_prior
        self.beta_prior = beta_prior
        logger.info(f"Initialized Bayesian analyzer with Beta prior: α={alpha_prior}, β={beta_prior}")
    
    def analyze_conversion(
        self,
        treatment_conversions: int,
        treatment_total: int,
        control_conversions: int,
        control_total: int,
        credible_interval: float = 0.95,
    ) -> Dict[str, Any]:
        """
        Bayesian analysis of conversion rates.
        
        Args:
            treatment_conversions: Number of conversions in treatment
            treatment_total: Total users in treatment
            control_conversions: Number of conversions in control
            control_total: Total users in control
            credible_interval: Credible interval level (default: 0.95)
            
        Returns:
            Dictionary with posterior distributions and statistics
        """
        # Posterior parameters (Beta update)
        alpha_treatment = self.alpha_prior + treatment_conversions
        beta_treatment = self.beta_prior + (treatment_total - treatment_conversions)
        
        alpha_control = self.alpha_prior + control_conversions
        beta_control = self.beta_prior + (control_total - control_conversions)
        
        # Posterior means
        treatment_mean = alpha_treatment / (alpha_treatment + beta_treatment)
        control_mean = alpha_control / (alpha_control + beta_control)
        
        # Posterior variances
        treatment_var = (alpha_treatment * beta_treatment) / ((alpha_treatment + beta_treatment) ** 2 * (alpha_treatment + beta_treatment + 1))
        control_var = (alpha_control * beta_control) / ((alpha_control + beta_control) ** 2 * (alpha_control + beta_control + 1))
        
        # Credible intervals
        alpha_level = (1 - credible_interval) / 2
        treatment_ci = stats.beta.ppf([alpha_level, 1 - alpha_level], alpha_treatment, beta_treatment)
        control_ci = stats.beta.ppf([alpha_level, 1 - alpha_level], alpha_control, beta_control)
        
        # Lift distribution (treatment vs control)
        # Sample from posteriors to estimate lift distribution
        np.random.seed(42)
        samples_treatment = np.random.beta(alpha_treatment, beta_treatment, 10000)
        samples_control = np.random.beta(alpha_control, beta_control, 10000)
        
        lift_samples = (samples_treatment - samples_control) / samples_control * 100
        
        # P(treatment > control)
        prob_treatment_better = np.mean(samples_treatment > samples_control)
        
        # Expected lift
        expected_lift = (treatment_mean - control_mean) / control_mean * 100
        
        # Credible interval for lift
        lift_ci = np.percentile(lift_samples, [alpha_level * 100, (1 - alpha_level) * 100])
        
        results = {
            "treatment_posterior_mean": treatment_mean,
            "control_posterior_mean": control_mean,
            "treatment_posterior_var": treatment_var,
            "control_posterior_var": control_var,
            "treatment_credible_interval": treatment_ci,
            "control_credible_interval": control_ci,
            "expected_lift_pct": expected_lift,
            "lift_credible_interval": lift_ci,
            "prob_treatment_better": prob_treatment_better,
            "alpha_treatment": alpha_treatment,
            "beta_treatment": beta_treatment,
            "alpha_control": alpha_control,
            "beta_control": beta_control,
            "lift_samples": lift_samples,
            "treatment_samples": samples_treatment,
            "control_samples": samples_control,
        }
        
        logger.info(
            f"Bayesian Conversion Analysis: "
            f"Treatment={treatment_mean:.4f}, Control={control_mean:.4f}, "
            f"Lift={expected_lift:.2f}%, P(T>C)={prob_treatment_better:.4f}"
        )
        
        return results
    
    def analyze_continuous(
        self,
        treatment_data: np.ndarray,
        control_data: np.ndarray,
        credible_interval: float = 0.95,
    ) -> Dict[str, Any]:
        """
        Bayesian analysis of continuous metrics (using normal distribution).
        
        Args:
            treatment_data: Array of treatment group values
            control_data: Array of control group values
            credible_interval: Credible interval level
            
        Returns:
            Dictionary with posterior distributions and statistics
        """
        treatment_mean = np.mean(treatment_data)
        treatment_var = np.var(treatment_data, ddof=1)
        control_mean = np.mean(control_data)
        control_var = np.var(control_data, ddof=1)
        
        n_treatment = len(treatment_data)
        n_control = len(control_data)
        
        # Posterior variance (normal model with known prior variance)
        treatment_post_var = treatment_var / n_treatment
        control_post_var = control_var / n_control
        
        # Credible intervals (normal approximation)
        alpha_level = (1 - credible_interval) / 2
        z_crit = stats.norm.ppf(1 - alpha_level)
        
        treatment_ci = [
            treatment_mean - z_crit * np.sqrt(treatment_post_var),
            treatment_mean + z_crit * np.sqrt(treatment_post_var),
        ]
        control_ci = [
            control_mean - z_crit * np.sqrt(control_post_var),
            control_mean + z_crit * np.sqrt(control_post_var),
        ]
        
        # Difference distribution
        diff_mean = treatment_mean - control_mean
        diff_var = treatment_post_var + control_post_var
        
        diff_ci = [
            diff_mean - z_crit * np.sqrt(diff_var),
            diff_mean + z_crit * np.sqrt(diff_var),
        ]
        
        # P(treatment > control) via sampling
        samples_treatment = np.random.normal(treatment_mean, np.sqrt(treatment_post_var), 10000)
        samples_control = np.random.normal(control_mean, np.sqrt(control_post_var), 10000)
        
        prob_treatment_better = np.mean(samples_treatment > samples_control)
        
        # Relative lift
        relative_lift = (treatment_mean - control_mean) / abs(control_mean) * 100 if control_mean != 0 else 0
        
        results = {
            "treatment_posterior_mean": treatment_mean,
            "control_posterior_mean": control_mean,
            "treatment_posterior_var": treatment_post_var,
            "control_posterior_var": control_post_var,
            "treatment_credible_interval": treatment_ci,
            "control_credible_interval": control_ci,
            "difference_mean": diff_mean,
            "difference_credible_interval": diff_ci,
            "relative_lift_pct": relative_lift,
            "prob_treatment_better": prob_treatment_better,
            "treatment_samples": samples_treatment,
            "control_samples": samples_control,
        }
        
        logger.info(
            f"Bayesian Continuous Analysis: "
            f"Treatment={treatment_mean:.4f}, Control={control_mean:.4f}, "
            f"Lift={relative_lift:.2f}%, P(T>C)={prob_treatment_better:.4f}"
        )
        
        return results


def bayesian_summary(
    results: Dict[str, Any],
    metric_name: str = "Metric",
    analysis_type: str = "conversion",
) -> pd.DataFrame:
    """
    Create summary DataFrame of Bayesian analysis.
    
    Args:
        results: Dictionary from BayesianAnalyzer methods
        metric_name: Name of the metric
        analysis_type: Type of analysis ('conversion' or 'continuous')
        
    Returns:
        Summary DataFrame
    """
    if analysis_type == "conversion":
        summary = pd.DataFrame({
            "Metric": [metric_name],
            "Treatment Posterior": [results["treatment_posterior_mean"]],
            "Control Posterior": [results["control_posterior_mean"]],
            "Expected Lift %": [results["expected_lift_pct"]],
            "P(Treatment > Control)": [results["prob_treatment_better"]],
            "Lift 95% CI Lower": [results["lift_credible_interval"][0]],
            "Lift 95% CI Upper": [results["lift_credible_interval"][1]],
        })
    else:
        summary = pd.DataFrame({
            "Metric": [metric_name],
            "Treatment Mean": [results["treatment_posterior_mean"]],
            "Control Mean": [results["control_posterior_mean"]],
            "Difference": [results["difference_mean"]],
            "Relative Lift %": [results["relative_lift_pct"]],
            "P(Treatment > Control)": [results["prob_treatment_better"]],
            "Diff 95% CI Lower": [results["difference_credible_interval"][0]],
            "Diff 95% CI Upper": [results["difference_credible_interval"][1]],
        })
    
    return summary
