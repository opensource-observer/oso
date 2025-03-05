MODEL (
  name oso.stg_github__releases,
  kind FULL
);

WITH release_events AS (
  SELECT
    *
  FROM @oso_source('bigquery.oso.stg_github__events') AS ghe
  WHERE
    ghe.type = 'ReleaseEvent'
)
SELECT
  id AS id,
  created_at AS created_at,
  repo.id AS repository_id,
  repo.name AS repository_name,
  actor.id AS actor_id,
  actor.login AS actor_login,
  'RELEASE_PUBLISHED' AS "type"
FROM release_events