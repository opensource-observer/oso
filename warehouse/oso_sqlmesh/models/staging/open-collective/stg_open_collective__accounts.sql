MODEL (
  name oso.stg_open_collective__accounts,
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column created_at,
    batch_size 365,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
  ),
  partitioned_by (DAY("created_at")),
  start '2015-01-01',
  cron '@daily',
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
  ignored_rules (
    "incrementalmustdefinenogapsaudit",
  ),
  tags (
    "incremental"
  )
);

SELECT
  id,
  slug,
  name,
  type,
  github_handle,
  repository_url,
  created_at,
  updated_at,
  stats.total_amount_received.currency AS total_amount_received_currency,
  CAST(stats.total_amount_received.value AS DOUBLE) AS total_amount_received_value
FROM @oso_source('bigquery.open_collective.accounts')
