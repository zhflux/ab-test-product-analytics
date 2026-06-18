# ab-test-product-analytics

End-to-end A/B test analysis for product experimentation with frequentist, Bayesian, and variance-reduction methods.

**Features**: Data ingestion, quality validation, SQL modeling, statistical testing (Frequentist + Bayesian + CUPED), cohort analysis, and interactive dashboard.

## Business Context

This project analyzes an A/B test comparing two versions of a page:
- `control` / `old_page`
- `treatment` / `new_page`

**Primary Hypothesis**: The new page version will increase conversion rate.

### Key Performance Indicators (KPI)
- Conversion rate (`conversion_rate`) by variation
- Absolute and relative uplift
- Revenue per user
- Conversion rate by page and country

## Project Overview

### Core Components
- `pipeline/ingest.py` — Data ingestion with validation (synthetic + Kaggle support)
- `pipeline/config.py` — Configuration management & structured logging
- `pipeline/data_validation.py` — Data quality checks
- `sql/staging.sql` — Event normalization model
- `sql/marts.sql` — Analytics aggregation models

### Analysis Methods
- `notebooks/ab_test_analysis.py` — Frequentist A/B testing (z-tests, confidence intervals)
- `notebooks/ab_test_eda.py` — Exploratory data analysis
- `notebooks/bayesian_analysis.py` — **Bayesian posterior analysis** (new)
- `notebooks/cuped_analysis.py` — **CUPED variance reduction** (new)
- `notebooks/cohort_analysis.py` — **Cohort retention tracking** (new)

### Dashboard & Tools
- `dashboard/app.py` — **Streamlit interactive dashboard** (new)
- `tests/test_middle_level.py` — Tests for advanced statistical methods (new)
- `.github/workflows/ci.yml` — CI/CD with data quality checks (updated)

## Getting Started

### Installation

```bash
python -m pip install -r requirements.txt
```

### Data Ingestion

**Synthetic data** (for development):
```bash
python pipeline/ingest.py --seed 2026 --num-users 5000
```

**Real Kaggle data**:
```bash
python pipeline/ingest.py --kaggle-ab data/ab_test.csv --kaggle-countries data/countries_ab.csv
```

**Output**: 
- CSV file: `data/raw_ab_test_events.csv`
- SQLite DB: `data/ab_test.db`
- Validation report (printed to console)

### Analysis Methods

#### 1. Frequentist A/B Testing
```bash
python notebooks/ab_test_analysis.py --database data/ab_test.db
```

Outputs:
- Variation-level summaries
- Conversion statistics with p-values
- Revenue per user analysis
- CSVs saved to `reports/`

#### 2. Interactive Streamlit Dashboard (NEW)
```bash
streamlit run dashboard/app.py
```

Access at `http://localhost:8501`

**Pages**:
- **Overview**: Key metrics and time series
- **Frequentist**: Z-tests with p-values
- **Bayesian**: Posterior distributions & P(T > C)
- **CUPED**: Variance-reduced estimates
- **Cohort**: Retention and value by cohort age
- **Comparison**: Side-by-side variation metrics

#### 3. Bayesian Analysis (NEW)
```python
from notebooks.bayesian_analysis import BayesianAnalyzer

analyzer = BayesianAnalyzer()
results = analyzer.analyze_conversion(
    treatment_conversions=50,
    treatment_total=500,
    control_conversions=30,
    control_total=500
)
print(f"P(Treatment > Control) = {results['prob_treatment_better']:.4f}")
```

#### 4. CUPED - Variance Reduction (NEW)
```python
from notebooks.cuped_analysis import estimate_theta, calculate_cuped_adjusted_metrics

theta = estimate_theta(historical_data, 'metric', 'covariate')
t_adj, c_adj, stats = calculate_cuped_adjusted_metrics(
    treatment_df, control_df, 'revenue', 'pre_revenue', theta
)
print(f"Variance reduction: {stats['variance_reduction_pct']:.1f}%")
```

#### 5. Cohort Analysis (NEW)
```python
from notebooks.cohort_analysis import create_cohorts, cohort_retention_analysis

cohort_df = create_cohorts(events_df, 'user_id', 'timestamp')
results = cohort_retention_analysis(cohort_df, user_col='user_id')
print(results['retention'])  # Retention patterns
```

#### 6. Exploratory Data Analysis
```bash
python notebooks/ab_test_eda.py --database data/ab_test.db
```

Generates visualizations and data quality report.

### Testing

```bash
# Run all tests
python -m pytest -v

# Run with coverage report
python -m pytest --cov=pipeline --cov=notebooks -v

# Test advanced statistical methods
python -m pytest tests/test_middle_level.py -v
```

**Test Coverage**:
- 15 tests across data validation, analysis methods, and pipeline
- Coverage for CUPED, Bayesian, Cohort analyses
- Data validation test suite

## Output Files

### Data
- `data/raw_ab_test_events.csv` — Raw events table
- `data/ab_test.db` — SQLite analytics database

### Reports
- `reports/ab_test_analysis_summary.csv` — Variation-level metrics
- `reports/ab_test_analysis_by_page.csv` — Page-level metrics
- `reports/ab_test_analysis_by_country.csv` — Country-level metrics
- `reports/ab_test_data_quality.csv` — Data quality report
- `reports/*.png` — Visualization charts

## Documentation

- [ADVANCED_FEATURES_GUIDE.md](ADVANCED_FEATURES_GUIDE.md) — **Comprehensive guide to advanced statistical methods** ⭐
- [DATA_DICTIONARY.md](DATA_DICTIONARY.md) — Field descriptions and semantics
- [dashboard/README.md](dashboard/README.md) — BI dashboard guidance

## Key Features

✅ **Data Quality**
- Automatic validation on ingest
- Missing value detection
- Distribution checks
- Duplicate detection

✅ **Multiple Statistical Approaches**
- Frequentist: p-values, confidence intervals
- Bayesian: posterior distributions, credible intervals
- CUPED: variance reduction using covariates
- Cohort: temporal effect tracking

✅ **Interactive Dashboard**
- Real-time exploration
- Multiple visualization types
- Variation comparison
- Export-ready reports

✅ **Production Ready**
- Structured logging
- Configuration management
- Comprehensive testing (15 tests)
- CI/CD with data quality checks
- Type hints throughout

✅ **Enterprise Grade**
- SQL-based analytics models
- Scalable architecture
- Version-controlled experiments
- Audit trail in database
