{#
  Turns all watch events into push events
#}

WITH watch_events AS (
    SELECT * 
    FROM {{ ref('stg_github__events') }} as ghe
    WHERE ghe.type IN ("WatchEvent", "ForkEvent")
)
SELECT
  we.id AS id,
  we.created_at AS created_at,
  we.repo.id AS repository_id,
  we.repo.name AS repository_name,
  we.actor.id AS actor_id,
  we.actor.login AS actor_login,
  CASE we.type
    WHEN "WatchEvent" THEN "STARRED"
    WHEN "ForkEvent" THEN "FORKED"
  END as type
FROM watch_events AS we