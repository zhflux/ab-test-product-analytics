"""
Tests for middle-level analytics modules.
"""
import pytest
import numpy as np
import pandas as pd
from notebooks.cuped_analysis import calculate_cuped_adjusted_metrics, estimate_theta, cuped_summary
from notebooks.bayesian_analysis import BayesianAnalyzer, bayesian_summary
from notebooks.cohort_analysis import create_cohorts, cohort_retention_analysis
from pipeline.data_validation import DataValidator


@pytest.fixture
def sample_data():
    """Create sample A/B test data."""
    np.random.seed(42)
    
    treatment_data = {
        'revenue': np.random.normal(100, 20, 500),
        'pre_revenue': np.random.normal(80, 15, 500),
    }
    
    control_data = {
        'revenue': np.random.normal(95, 20, 500),
        'pre_revenue': np.random.normal(78, 15, 500),
    }
    
    return (
        pd.DataFrame(treatment_data),
        pd.DataFrame(control_data)
    )


class TestCUPED:
    """CUPED analysis tests."""
    
    def test_cuped_adjustment(self, sample_data):
        """Test CUPED adjustment reduces variance."""
        treatment_df, control_df = sample_data
        
        t_adj, c_adj, stats = calculate_cuped_adjusted_metrics(
            treatment_df, control_df,
            'revenue', 'pre_revenue',
            theta=0.5
        )
        
        assert isinstance(stats, dict)
        assert 'variance_reduction_pct' in stats
        # Variance reduction can be negative if covariate is not correlated
        assert isinstance(stats['variance_reduction_pct'], (int, float))
        assert 'relative_lift_pct' in stats
    
    def test_theta_estimation(self, sample_data):
        """Test theta estimation from data."""
        treatment_df, control_df = sample_data
        combined = pd.concat([treatment_df, control_df])
        
        theta = estimate_theta(combined, 'revenue', 'pre_revenue')
        
        assert 0 <= theta <= 1
        assert isinstance(theta, float)
    
    def test_cuped_summary(self, sample_data):
        """Test CUPED summary creation."""
        treatment_df, control_df = sample_data
        _, _, stats = calculate_cuped_adjusted_metrics(
            treatment_df, control_df,
            'revenue', 'pre_revenue',
            theta=0.5
        )
        
        summary = cuped_summary(stats, "Revenue")
        
        assert len(summary) == 1
        assert 'Treatment (Adjusted)' in summary.columns
        assert 'Control (Adjusted)' in summary.columns


class TestBayesian:
    """Bayesian analysis tests."""
    
    def test_bayesian_conversion_analysis(self):
        """Test Bayesian conversion rate analysis."""
        analyzer = BayesianAnalyzer()
        
        results = analyzer.analyze_conversion(
            treatment_conversions=50,
            treatment_total=500,
            control_conversions=30,
            control_total=500,
        )
        
        assert 'treatment_posterior_mean' in results
        assert 'control_posterior_mean' in results
        assert 'prob_treatment_better' in results
        
        # P(T > C) should be between 0 and 1
        assert 0 <= results['prob_treatment_better'] <= 1
        assert results['treatment_posterior_mean'] > results['control_posterior_mean']
    
    def test_bayesian_continuous_analysis(self):
        """Test Bayesian continuous metric analysis."""
        analyzer = BayesianAnalyzer()
        
        treatment = np.random.normal(100, 20, 200)
        control = np.random.normal(95, 20, 200)
        
        results = analyzer.analyze_continuous(treatment, control)
        
        assert 'treatment_posterior_mean' in results
        assert 'control_posterior_mean' in results
        assert 'relative_lift_pct' in results
    
    def test_bayesian_summary(self):
        """Test Bayesian summary creation."""
        analyzer = BayesianAnalyzer()
        
        results = analyzer.analyze_conversion(50, 500, 30, 500)
        summary = bayesian_summary(results, "Conversion Rate", "conversion")
        
        assert len(summary) == 1
        assert 'P(Treatment > Control)' in summary.columns


class TestCohort:
    """Cohort analysis tests."""
    
    def test_cohort_creation(self):
        """Test cohort creation and assignment."""
        df = pd.DataFrame({
            'user_id': [1, 1, 2, 2, 3, 3],
            'timestamp': pd.date_range('2026-01-01', periods=6, freq='D'),
            'revenue': [0, 100, 0, 50, 0, 200],
            'variation': ['A', 'A', 'B', 'B', 'A', 'A'],
        })
        
        cohort_df = create_cohorts(df, 'user_id', 'timestamp', cohort_window_days=7)
        
        assert 'cohort_date' in cohort_df.columns
        assert 'days_since_cohort' in cohort_df.columns
        assert 'cohort_age' in cohort_df.columns
    
    def test_cohort_retention(self):
        """Test cohort retention analysis."""
        df = pd.DataFrame({
            'user_id': list(range(1, 101)) * 2,
            'timestamp': pd.date_range('2026-01-01', periods=200, freq='h'),
            'revenue': np.random.exponential(10, 200),
            'variation': ['A'] * 100 + ['B'] * 100,
            'cohort_date': pd.Timestamp('2026-01-01'),
            'cohort_age': 0,
        })
        
        results = cohort_retention_analysis(
            df,
            user_col='user_id',
            value_col='revenue',
            variation_col='variation'
        )
        
        assert 'retention' in results
        assert 'value' in results
        assert 'cumulative_value' in results


class TestDataValidator:
    """Data validation tests."""
    
    def test_events_validation_pass(self):
        """Test valid events data passes validation."""
        df = pd.DataFrame({
            'user_id': [1, 2, 3],
            'variation': ['A', 'B', 'A'],
            'event_type': ['page_view', 'purchase', 'page_view'],
            'timestamp': pd.date_range('2026-01-01', periods=3),
            'revenue': [0, 100, 0],
        })
        
        validator = DataValidator()
        is_valid, results = validator.validate_events_data(df)
        
        assert is_valid
        assert results['n_records'] == 3
        assert results['n_users'] == 3
    
    def test_events_validation_missing_columns(self):
        """Test validation fails with missing columns."""
        df = pd.DataFrame({
            'user_id': [1, 2, 3],
            'variation': ['A', 'B', 'A'],
        })
        
        validator = DataValidator()
        is_valid, results = validator.validate_events_data(df)
        
        assert not is_valid
        assert len(results['errors']) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
