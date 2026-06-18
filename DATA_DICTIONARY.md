# Data Dictionary

## Event schema (`raw_ab_test_events`)

- `event_id` — unique identifier for each event row.
- `user_id` — identifier for the user associated with the event.
- `experiment_name` — name of the experimental test; synthetic data uses `checkout_redesign`, Kaggle ingestion uses `kaggle_ab_test`.
- `variation` — experiment group, usually `control` or `treatment`.
- `page` — page variant, typically `old_page` or `new_page`.
- `event_date` — timestamp of the event in `YYYY-MM-DD HH:MM:SS` format.
- `event_type` — type of event, such as `session_start`, `page_view`, `signup`, or `purchase`.
- `revenue` — numeric revenue amount for purchase events; zero for non-purchase events.
- `session_id` — identifier for the user session.
- `country` — country code associated with the user (e.g. `US`, `UK`).

## Kaggle source fields

- `id` — unique record identifier from Kaggle source.
- `time` — session time as `MM:SS.s` string.
- `con_treat` — experiment group label in Kaggle dataset.
- `page` — source page variant field from Kaggle dataset.
- `converted` — binary conversion indicator from Kaggle dataset.
- `country` — country code from Kaggle `countries_ab.csv`.

## Notes

- `page` and `country` are added to synthetic data for more realistic segmentation.
- `event_type` is derived from `converted` in Kaggle ingestion: `purchase` for conversion, `page_view` otherwise.
- `revenue` is represented as numeric and matches the conversion indicator for Kaggle data.
