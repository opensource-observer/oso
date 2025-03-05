MODEL (
  name oso.stg_github__stars_and_forks,
  kind FULL
);

WITH watch_events AS (
  SELECT
    *
  FROM @oso_source('bigquery.oso.stg_github__events') AS ghe
  WHERE
    ghe.type IN ('WatchEvent', 'ForkEvent')
)
SELECT
  we.id AS id,
  we.created_at AS created_at,
  we.repo.id AS repository_id,
  we.repo.name AS repository_name,
  we.actor.id AS actor_id,
  we.actor.login AS actor_login,
  CASE we.type WHEN 'WatchEvent' THEN 'STARRED' WHEN 'ForkEvent' THEN 'FORKED' END AS "type"
FROM watch_events AS we