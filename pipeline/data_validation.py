"""
Data validation for A/B test data.
Checks data quality and consistency before analysis.
"""
import logging
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates A/B test data quality."""
    
    def __init__(self, max_missing_pct: float = 0.05):
        """
        Initialize validator.
        
        Args:
            max_missing_pct: Maximum allowed missing data percentage
        """
        self.max_missing_pct = max_missing_pct
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_events_data(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """
        Validate events data structure and content.
        
        Args:
            df: Events DataFrame
            
        Returns:
            (is_valid, results_dict)
        """
        self.errors = []
        self.warnings = []
        results = {}
        
        # Check required columns
        required_cols = ['user_id', 'variation', 'event_type', 'timestamp', 'revenue']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            self.errors.append(f"Missing required columns: {missing_cols}")
            return False, {"errors": self.errors}
        
        # Check data types
        if not pd.api.types.is_integer_dtype(df['user_id']) and not pd.api.types.is_string_dtype(df['user_id']):
            self.warnings.append("user_id should be integer or string")
        
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            self.warnings.append("timestamp should be datetime type")
        
        if not (pd.api.types.is_numeric_dtype(df['revenue'])):
            self.warnings.append("revenue should be numeric type")
        
        # Check for missing values
        missing_pcts = (df.isnull().sum() / len(df)) * 100
        high_missing = missing_pcts[missing_pcts > self.max_missing_pct]
        
        for col, pct in high_missing.items():
            self.errors.append(f"Column {col} has {pct:.2f}% missing values (max: {self.max_missing_pct}%)")
        
        # Check for negative revenue
        if (df['revenue'] < 0).any():
            self.warnings.append(f"Found {(df['revenue'] < 0).sum()} records with negative revenue")
        
        # Check for invalid timestamps
        if df['timestamp'].isnull().any():
            self.errors.append("Found null timestamps")
        
        # Check variation values
        variations = df['variation'].unique()
        if len(variations) < 2:
            self.errors.append(f"Expected at least 2 variations, found {len(variations)}")
        
        # Check event types
        event_types = df['event_type'].unique()
        valid_events = {'page_view', 'conversion', 'purchase', 'click', 'view'}
        invalid_events = set(event_types) - valid_events
        if invalid_events:
            self.warnings.append(f"Found unexpected event types: {invalid_events}")
        
        # Check minimum sample sizes
        users_per_var = df.groupby('variation')['user_id'].nunique()
        if (users_per_var < 100).any():
            self.warnings.append(f"Some variations have < 100 users: {users_per_var[users_per_var < 100].to_dict()}")
        
        results = {
            "n_records": len(df),
            "n_users": df['user_id'].nunique(),
            "n_variations": len(variations),
            "n_events": len(event_types),
            "date_range": (df['timestamp'].min(), df['timestamp'].max()),
            "variations": list(variations),
            "event_types": list(event_types),
            "users_per_variation": users_per_var.to_dict(),
            "missing_pct": missing_pcts.to_dict(),
            "errors": self.errors,
            "warnings": self.warnings,
        }
        
        is_valid = len(self.errors) == 0
        
        for error in self.errors:
            logger.error(f"Validation Error: {error}")
        for warning in self.warnings:
            logger.warning(f"Validation Warning: {warning}")
        
        return is_valid, results
    
    def validate_user_data(self, df: pd.DataFrame) -> Tuple[bool, Dict]:
        """
        Validate user data.
        
        Args:
            df: User DataFrame
            
        Returns:
            (is_valid, results_dict)
        """
        self.errors = []
        self.warnings = []
        results = {}
        
        required_cols = ['user_id', 'variation', 'country']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            self.errors.append(f"Missing required columns: {missing_cols}")
            return False, {"errors": self.errors}
        
        # Check for duplicates
        duplicates = df[df.duplicated(subset=['user_id'], keep=False)]
        if len(duplicates) > 0:
            self.warnings.append(f"Found {len(duplicates)} duplicate user_ids")
        
        # Check assignment balance
        variation_counts = df['variation'].value_counts()
        expected_pct = 100 / len(variation_counts)
        
        for var, count in variation_counts.items():
            actual_pct = (count / len(df)) * 100
            if abs(actual_pct - expected_pct) > 10:
                self.warnings.append(
                    f"Variation {var} has {actual_pct:.1f}% (expected ~{expected_pct:.1f}%)"
                )
        
        results = {
            "n_users": len(df),
            "n_variations": df['variation'].nunique(),
            "n_countries": df['country'].nunique(),
            "variation_distribution": variation_counts.to_dict(),
            "errors": self.errors,
            "warnings": self.warnings,
        }
        
        is_valid = len(self.errors) == 0
        
        return is_valid, results


def run_data_quality_checks(events_df: pd.DataFrame, user_df: Optional[pd.DataFrame] = None) -> Dict:
    """
    Run comprehensive data quality checks.
    
    Args:
        events_df: Events DataFrame
        user_df: Optional user DataFrame
        
    Returns:
        Dictionary with all validation results
    """
    validator = DataValidator()
    
    results = {
        "timestamp": pd.Timestamp.now(),
        "events_validation": None,
        "user_validation": None,
    }
    
    # Validate events
    is_valid, events_results = validator.validate_events_data(events_df)
    results["events_validation"] = {
        "is_valid": is_valid,
        "results": events_results,
    }
    
    # Validate users if provided
    if user_df is not None:
        is_valid, user_results = validator.validate_user_data(user_df)
        results["user_validation"] = {
            "is_valid": is_valid,
            "results": user_results,
        }
    
    return results


def print_validation_report(validation_results: Dict):
    """
    Print human-readable validation report.
    
    Args:
        validation_results: Dictionary from run_data_quality_checks
    """
    print("\n" + "="*60)
    print("DATA QUALITY VALIDATION REPORT")
    print("="*60)
    
    if validation_results["events_validation"]:
        print("\nEVENTS DATA:")
        ev = validation_results["events_validation"]["results"]
        print(f"  Records: {ev['n_records']}")
        print(f"  Unique Users: {ev['n_users']}")
        print(f"  Variations: {ev['variations']}")
        print(f"  Date Range: {ev['date_range']}")
        
        if ev['errors']:
            print("\n  ❌ ERRORS:")
            for err in ev['errors']:
                print(f"    - {err}")
        
        if ev['warnings']:
            print("\n  ⚠️  WARNINGS:")
            for warn in ev['warnings']:
                print(f"    - {warn}")
        
        if not ev['errors']:
            print("\n  ✓ Events data passed validation")
    
    if validation_results["user_validation"]:
        print("\nUSER DATA:")
        uv = validation_results["user_validation"]["results"]
        print(f"  Users: {uv['n_users']}")
        print(f"  Variations: {uv['n_variations']}")
        print(f"  Countries: {uv['n_countries']}")
        
        if uv['errors']:
            print("\n  ❌ ERRORS:")
            for err in uv['errors']:
                print(f"    - {err}")
        
        if uv['warnings']:
            print("\n  ⚠️  WARNINGS:")
            for warn in uv['warnings']:
                print(f"    - {warn}")
        
        if not uv['errors']:
            print("\n  ✓ User data passed validation")
    
    print("\n" + "="*60 + "\n")
