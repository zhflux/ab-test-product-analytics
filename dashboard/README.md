# Power BI Dashboard Guidance

This folder contains guidance for building a Power BI dashboard from the generated A/B test dataset.

## Data sources

Use one of the following sources:
- `data/raw_ab_test_events.csv`
- `data/ab_test.db` (SQLite)

## Recommended report structure

1. Load the raw event table into Power BI.
2. Create a staging query or view equivalent to `sql/staging.sql`.
3. Build mart queries equivalent to `sql/marts.sql`.

## Key metrics to visualize

- Users by variation
- Conversions by variation
- Conversion rate by variation
- Absolute and relative uplift
- Revenue per user by variation
- Conversion rate by page and by country
- Page-level conversion performance
- Country-level conversion performance

## Dashboard visuals

- Bar chart: conversion rate by variation
- Bar chart: conversion rate by page and variation
- Bar chart: conversion rate by country and variation
- Cards: total users, conversions, revenue per user
- Table: summarized metrics for variation/page/country

## Notes

The dataset is structured for experiment analysis with the following fields:
- `variation` — experiment group (`control` / `treatment`)
- `page` — page variant (`old_page`, `new_page`)
- `country` — user location
- `event_type` — event classification (`page_view`, `purchase`)
- `revenue` — numeric target for purchase events

Use the staging and mart layers to avoid direct raw table joins in Power BI.
