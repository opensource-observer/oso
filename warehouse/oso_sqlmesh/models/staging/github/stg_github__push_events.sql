MODEL (
  name oso.stg_github__push_events,
  description 'Gathers all github events for all github artifacts',
  kind FULL,
  dialect trino
);

SELECT
  ghe.created_at AS created_at,
  ghe.repo.id AS repository_id,
  ghe.repo.name AS repository_name,
  ghe.actor.id AS actor_id,
  ghe.actor.login AS actor_login,
  JSON_EXTRACT_SCALAR(ghe.payload, '$.push_id') AS push_id,
  JSON_EXTRACT_SCALAR(ghe.payload, '$.ref') AS ref,
  JSON_FORMAT(JSON_EXTRACT(ghe.payload, '$.commits')) AS commits,
  JSON_ARRAY_LENGTH(JSON_FORMAT(JSON_EXTRACT(ghe.payload, '$.commits'))) AS available_commits_count,
  CAST(JSON_EXTRACT(ghe.payload, '$.distinct_size') AS INTEGER) AS actual_commits_count
FROM @oso_source('bigquery.oso.stg_github__events') AS ghe
WHERE
  ghe.type = 'PushEvent'