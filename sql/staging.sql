-- Staging layer for raw A/B test experiment events.

DROP VIEW IF EXISTS stg_ab_test_events;
CREATE VIEW stg_ab_test_events AS
SELECT
    event_id,
    user_id,
    experiment_name,
    variation,
    page,
    DATE(event_date) AS event_date,
    event_type,
    revenue,
    session_id,
    country
FROM raw_ab_test_events;
