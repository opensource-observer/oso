MODEL (
  name oso.stg_ossd__current_repositories,
  description 'The most recent view of repositories from the ossd repositories dagster source',
  dialect trino,
  kind FULL,
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH ranked_repositories AS (
  SELECT
    node_id,
    id::TEXT AS id,
    LOWER(url) AS url,
    LOWER(name) AS name,
    LOWER(name_with_owner) AS name_with_owner,
    LOWER(owner) AS owner,
    LOWER(branch) AS branch,
    star_count,
    watcher_count,
    fork_count,
    is_fork,
    license_name,
    license_spdx_id,
    language,
    created_at,
    updated_at,
    ingestion_time,
    ROW_NUMBER() OVER (PARTITION BY node_id ORDER BY ingestion_time DESC, id ASC) AS row_num
  FROM @oso_source('bigquery.ossd.repositories')
)
SELECT
  node_id,
  id,
  url,
  name,
  name_with_owner,
  owner,
  branch,
  star_count,
  watcher_count,
  fork_count,
  is_fork,
  license_name,
  license_spdx_id,
  language,
  created_at,
  updated_at,
  ingestion_time
FROM ranked_repositories
WHERE
  row_num = 1