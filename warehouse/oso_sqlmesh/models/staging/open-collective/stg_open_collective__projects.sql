MODEL (
  name oso.stg_open_collective__projects,
  dialect trino,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 2,
    lookback 31,
    forward_only true,
  ),
  partitioned_by (DAY("time")),
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
  UNNEST(@json_extract_from_array(to_account, '$.socialLinks')) as link
  WHERE JSON_EXTRACT_SCALAR(link, '$.url') LIKE '%github.com%'
)

SELECT
  created_at AS time,
  LOWER(JSON_EXTRACT_SCALAR(to_account, '$.slug')) as account_slug,
  LOWER(JSON_EXTRACT_SCALAR(link, '$.url')) as artifact_url,
  REGEXP_EXTRACT(LOWER(JSON_EXTRACT_SCALAR(link, '$.url')), 'github\\.com/([a-z0-9-]+)') as artifact_namespace,
  REGEXP_EXTRACT(
    LOWER(JSON_EXTRACT_SCALAR(link, '$.url')), 
    'github\\.com/[a-z0-9-]+/([a-z0-9-._]+)'
  ) as artifact_name,
  JSON_EXTRACT_SCALAR(to_account, '$.name') AS account_name,
  JSON_EXTRACT_SCALAR(to_account, '$.type') AS account_type,
  JSON_EXTRACT_SCALAR(to_account, '$.id') AS account_id
FROM social_links