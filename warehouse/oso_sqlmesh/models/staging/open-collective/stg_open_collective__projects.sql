MODEL (
  name oso.stg_open_collective__projects,
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column created_at,
    batch_size 365,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
  ),
  partitioned_by (DAY(created_at)),
  start '2015-01-01',
  cron '@weekly',
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

WITH social_links AS (
  SELECT 
    created_at,
    to_account,
    link
  FROM @oso_source('bigquery.open_collective.deposits'),
  UNNEST(@json_extract_from_array(JSON_EXTRACT(to_account, '$.socialLinks'), '$')) as link
  WHERE JSON_EXTRACT_SCALAR(link, '$.url') LIKE '%github.com%'
)

SELECT
  created_at,
  LOWER(JSON_EXTRACT_SCALAR(to_account, '$.slug')) as account_slug,
  LOWER(JSON_EXTRACT_SCALAR(link, '$.url')) as social_link_url,
  JSON_EXTRACT_SCALAR(to_account, '$.name') AS account_name,
  JSON_EXTRACT_SCALAR(to_account, '$.type') AS account_type,
  JSON_EXTRACT_SCALAR(to_account, '$.id') AS account_id
FROM social_links