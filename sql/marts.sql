-- Mart layer for experiment performance and A/B test metrics.

DROP VIEW IF EXISTS mart_experiment_summary;
CREATE VIEW mart_experiment_summary AS
SELECT
    variation,
    COUNT(DISTINCT user_id) AS users,
    SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS conversions,
    ROUND(SUM(CASE WHEN event_type = 'purchase' THEN 1.0 ELSE 0.0 END) / COUNT(DISTINCT user_id), 4) AS conversion_rate,
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(revenue) / NULLIF(COUNT(DISTINCT user_id), 0), 2) AS revenue_per_user,
    ROUND(SUM(revenue) / NULLIF(SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END), 0), 2) AS revenue_per_conversion
FROM stg_ab_test_events
GROUP BY variation;

DROP VIEW IF EXISTS mart_experiment_by_page;
CREATE VIEW mart_experiment_by_page AS
SELECT
    variation,
    page,
    COUNT(DISTINCT user_id) AS users,
    SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS conversions,
    ROUND(SUM(CASE WHEN event_type = 'purchase' THEN 1.0 ELSE 0.0 END) / COUNT(DISTINCT user_id), 4) AS conversion_rate,
    ROUND(SUM(revenue), 2) AS total_revenue
FROM stg_ab_test_events
GROUP BY variation, page;

DROP VIEW IF EXISTS mart_experiment_by_country;
CREATE VIEW mart_experiment_by_country AS
SELECT
    variation,
    country,
    COUNT(DISTINCT user_id) AS users,
    SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS conversions,
    ROUND(SUM(CASE WHEN event_type = 'purchase' THEN 1.0 ELSE 0.0 END) / COUNT(DISTINCT user_id), 4) AS conversion_rate,
    ROUND(SUM(revenue), 2) AS total_revenue
FROM stg_ab_test_events
GROUP BY variation, country;
