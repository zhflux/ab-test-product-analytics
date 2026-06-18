# A/B Test Analytics - Advanced Features Guide

## Overview

This project includes a production-ready A/B testing analytics platform with advanced statistical methods, interactive dashboards, and enterprise-grade infrastructure.

## New Features

### 1. Statistical Methods

#### 🎯 CUPED Analysis (`notebooks/cuped_analysis.py`)
**Controlled-Experiment Using Pre-Experiment Data**

Reduces variance and increases statistical power by using historical user behavior:

```python
from notebooks.cuped_analysis import calculate_cuped_adjusted_metrics, estimate_theta

# Estimate optimal control factor
theta = estimate_theta(historical_data, 'metric', 'covariate')

# Calculate CUPED-adjusted metrics
t_adj, c_adj, stats = calculate_cuped_adjusted_metrics(
    treatment_df, control_df,
    metric_col='revenue',
    covariate_col='pre_revenue',
    theta=theta
)

# Results show variance reduction
print(f"Variance reduction: {stats['variance_reduction_pct']:.1f}%")
print(f"Adjusted lift: {stats['relative_lift_pct']:.2f}%")
```

**Use Case**: When you need tighter confidence intervals with the same sample size.

---

#### 🔮 Bayesian Analysis (`notebooks/bayesian_analysis.py`)
**Probabilistic A/B Testing with Posterior Distributions**

Alternative to frequentist testing with intuitive probabilistic interpretation:

```python
from notebooks.bayesian_analysis import BayesianAnalyzer

analyzer = BayesianAnalyzer(alpha_prior=1.0, beta_prior=1.0)

# For conversion rates
results = analyzer.analyze_conversion(
    treatment_conversions=50,
    treatment_total=500,
    control_conversions=30,
    control_total=500
)

# Get probabilistic answers
print(f"P(Treatment > Control) = {results['prob_treatment_better']:.4f}")
print(f"Expected lift: {results['expected_lift_pct']:.2f}%")

# For continuous metrics (revenue, time spent, etc)
results = analyzer.analyze_continuous(treatment_data, control_data)
print(f"P(Treatment > Control) = {results['prob_treatment_better']:.4f}")
```

**Advantages**:
- Direct probability statements (no p-value misinterpretation)
- Flexible prior specifications
- Natural credible intervals (vs confidence intervals)
- Can make sequential decisions without multiple testing correction

---

#### 📊 Cohort Analysis (`notebooks/cohort_analysis.py`)
**Temporal User Behavior Tracking**

Understand how user behavior evolves over time by cohort:

```python
from notebooks.cohort_analysis import create_cohorts, cohort_retention_analysis

# Create cohorts based on first activity
cohort_df = create_cohorts(
    events_df,
    user_col='user_id',
    timestamp_col='timestamp',
    cohort_window_days=7
)

# Analyze retention and value
results = cohort_retention_analysis(
    cohort_df,
    user_col='user_id',
    value_col='revenue',
    variation_col='variation'
)

# View retention patterns
print(results['retention'])      # Users per cohort age
print(results['cumulative_value']) # Total value by cohort
```

**Insights**:
- Identify early vs late cohort trends
- Detect cohort effects
- Measure long-term treatment impact

---

### 2. Data Quality & Validation

#### 📋 Data Validation (`pipeline/data_validation.py`)

Comprehensive data quality checks before analysis:

```python
from pipeline.data_validation import run_data_quality_checks, print_validation_report

# Run all validations
results = run_data_quality_checks(events_df)

# Get detailed report
print_validation_report(results)
```

**Checks**:
- ✓ Required columns presence
- ✓ Data type validation
- ✓ Missing value detection (< 5%)
- ✓ Variation assignment balance
- ✓ Minimum sample size requirements
- ✓ Data range validation
- ✓ Duplicate detection

---

### 3. Interactive Dashboard

#### 🎨 Streamlit Dashboard (`dashboard/app.py`)

Launch the interactive analytics dashboard:

```bash
streamlit run dashboard/app.py
```

**Pages**:
1. **Overview**: Key metrics and time series
2. **Frequentist Analysis**: Traditional z-tests
3. **Bayesian Analysis**: Posterior distributions
4. **CUPED Analysis**: Variance-reduced estimates
5. **Cohort Analysis**: Temporal patterns
6. **Comparison**: Side-by-side variation metrics

---

### 4. Configuration Management

#### ⚙️ Settings (`pipeline/config.py`)

Centralized configuration with sensible defaults:

```python
from pipeline.config import settings

print(settings.data_dir)           # Data directory
print(settings.confidence_level)   # 0.95
print(settings.significance_level) # 0.05
print(settings.db_path)            # SQLite database path
```

---

### 5. Structured Logging

#### 📝 Logging (`pipeline/config.py`)

All operations logged with structured output:

```python
from pipeline.config import setup_logging

logger = setup_logging(__name__)
logger.info("Pipeline started")
logger.warning("Unexpected data type")
logger.error("Validation failed")
```

**Output**: 
```
2026-06-18 13:31:30,283 - __main__ - INFO - Starting ingestion pipeline
```

---

## Project Structure

```
ab-test-product-analytics/
├── pipeline/
│   ├── config.py              # Configuration & logging
│   ├── ingest.py              # Data ingestion with validation
│   └── data_validation.py      # Data quality checks
├── notebooks/
│   ├── ab_test_analysis.py     # Frequentist analysis
│   ├── ab_test_eda.py          # Exploratory data analysis
│   ├── bayesian_analysis.py    # Bayesian statistical methods
│   ├── cuped_analysis.py       # CUPED variance reduction
│   └── cohort_analysis.py      # Cohort retention analysis
├── dashboard/
│   ├── app.py                  # Streamlit interactive app
│   └── README.md               # BI guidance
├── sql/
│   ├── staging.sql             # Data staging views
│   └── marts.sql               # Analytics data marts
├── tests/
│   ├── test_ingest.py          # Ingestion tests
│   ├── test_analysis.py        # Analysis tests
│   └── test_middle_level.py    # Advanced statistical methods tests
└── .github/workflows/
    └── ci.yml                  # CI/CD with data quality checks
```

---

## Running the Project

### 1. Data Ingestion with Validation

```bash
# Generate synthetic data
python pipeline/ingest.py --seed 2026 --num-users 5000

# Load Kaggle data
python pipeline/ingest.py --kaggle-ab data/ab_test.csv --kaggle-countries data/countries_ab.csv
```

**Output**:
- CSV file with raw events
- SQLite database (`ab_test.db`)
- Data quality validation report

---

### 2. Run Analysis Pipeline

```bash
python notebooks/ab_test_analysis.py
python notebooks/ab_test_eda.py
```

**Outputs** saved to `reports/`:
- Variation summaries
- Conversion statistics
- Revenue analysis
- Visualizations

---

### 3. Start Interactive Dashboard

```bash
streamlit run dashboard/app.py
```

Opens at `http://localhost:8501`

---

### 4. Run Tests & CI

```bash
# Run all tests
python -m pytest -v

# Run with coverage
python -m pytest --cov=pipeline --cov=notebooks -v

# Test advanced statistical methods
python -m pytest tests/test_middle_level.py -v
```

---

## Advanced Usage

### Example: Complete CUPED Analysis

```python
import pandas as pd
from pipeline.ingest import load_kaggle_dataset
from notebooks.cuped_analysis import estimate_theta, calculate_cuped_adjusted_metrics, cuped_summary

# Load data
df = pd.read_csv('data/raw_ab_test_events.csv')

# Split by variation
treatment = df[df['variation'] == 'treatment']
control = df[df['variation'] == 'control']

# Estimate optimal theta from historical data
theta = estimate_theta(df, 'revenue', 'pre_experiment_spend')

# Calculate adjusted metrics
t_adj, c_adj, stats = calculate_cuped_adjusted_metrics(
    treatment, control,
    'revenue', 'pre_experiment_spend',
    theta=theta
)

# Get summary
summary = cuped_summary(stats, "Revenue")
print(summary)
```

---

### Example: Bayesian Multi-Variation Analysis

```python
from notebooks.bayesian_analysis import BayesianAnalyzer

analyzer = BayesianAnalyzer()

# Analyze each variation pair
for var1 in variations:
    for var2 in variations:
        if var1 != var2:
            v1_conversions = (df[df['variation'] == var1]['event_type'] == 'purchase').sum()
            v1_total = df[df['variation'] == var1]['user_id'].nunique()
            v2_conversions = (df[df['variation'] == var2]['event_type'] == 'purchase').sum()
            v2_total = df[df['variation'] == var2]['user_id'].nunique()
            
            results = analyzer.analyze_conversion(
                v1_conversions, v1_total,
                v2_conversions, v2_total
            )
            
            print(f"{var1} vs {var2}: P(v1 > v2) = {results['prob_treatment_better']:.4f}")
```

---

## Key Metrics & Interpretations

### Frequentist Approach
- **P-value < 0.05**: Reject null hypothesis (statistically significant)
- **Confidence Interval**: If we repeat experiment 100 times, 95 will fall in this range

### Bayesian Approach
- **P(Treatment > Control)**: Direct probability that treatment is better
- **Credible Interval**: 95% probability the true value lies in this range
- **Posterior Mean**: Best single point estimate given data and prior

### CUPED
- **Theta**: Fraction of variance explained by covariate (0-1)
- **Variance Reduction %**: % decrease in standard error (can be negative)
- **Adjusted Lift**: More precise estimate of true treatment effect

---

## Testing & CI/CD

### Local Testing
```bash
pytest tests/ -v
```

### GitHub Actions CI
Automatically runs on push to `main`:
- ✓ Dependency installation
- ✓ Unit tests with coverage
- ✓ Data generation
- ✓ Data quality validation

---

## Dependencies

### Core
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `scipy` - Statistical tests

### Analytics
- `scikit-learn` - Machine learning utilities
- `plotly` - Interactive visualizations

### Dashboard & UI
- `streamlit` - Interactive web app

### Infrastructure
- `python-dotenv` - Environment configuration
- `tqdm` - Progress bars
- `pytest` - Testing framework

---

## Best Practices

### 1. Always Validate Data First
```python
from pipeline.data_validation import run_data_quality_checks
results = run_data_quality_checks(df)
assert results['events_validation']['is_valid']
```

### 2. Use Type Hints
```python
from typing import Dict, Tuple
def analyze(
    df: pd.DataFrame, 
    metric: str
) -> Tuple[float, Dict]:
    ...
```

### 3. Log Important Operations
```python
from pipeline.config import setup_logging
logger = setup_logging(__name__)
logger.info(f"Processing {len(df)} records")
```

### 4. Test New Features
```python
pytest tests/test_middle_level.py::TestCUPED -v
```

---

## Common Questions

**Q: When should I use CUPED?**
A: When you have highly correlated pre-experiment data. It tightens confidence intervals without more samples.

**Q: Frequentist vs Bayesian?**
A: Use frequentist for standard reporting (stakeholders expect p-values). Use Bayesian when you want probability statements or sequential decisions.

**Q: How does cohort analysis help?**
A: Detects if treatment effect changes over time or if newer users behave differently than older cohorts.

---

## Next Steps

1. **Add ML Features**: Propensity scoring, heterogeneous treatment effects
2. **Extend Metrics**: Revenue per user, ROAS, retention curves
3. **Real-time Dashboard**: Use Streamlit Cloud or self-hosted
4. **A/B Testing Platform**: Integrate with experiment platform APIs

---

## Resources

- [Bayesian A/B Testing](https://www.evanmiller.org/bayesian-ab-testing.html)
- [CUPED Paper](https://arxiv.org/abs/1909.06245)
- [Cohort Analysis Guide](https://www.mixpanel.com/blog/2013/11/01/cohort-analysis-why-its-awesome-and-how-to-use-it/)

---

**Created**: June 18, 2026  
**Maintainer**: Your Team
