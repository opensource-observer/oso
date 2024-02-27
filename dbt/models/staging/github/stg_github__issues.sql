{#
  Turns all watch events into push events
#}

WITH issue_events AS (
    SELECT * 
    FROM {{ ref('stg_github__events') }} as ghe
    WHERE ghe.type = "IssuesEvent"
)
SELECT
  ie.id AS id,
  ie.created_at AS created_at,
  ie.repo.id AS repository_id,
  ie.repo.name AS repository_name,
  ie.actor.id AS actor_id,
  ie.actor.login AS actor_login,
  CONCAT("ISSUE_", UPPER(JSON_VALUE(ie.payload, "$.action"))) as type
FROM issue_events AS ie