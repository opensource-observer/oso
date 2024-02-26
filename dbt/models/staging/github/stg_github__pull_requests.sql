{#
  Turns all watch events into push events
#}

WITH pull_request_events AS (
    SELECT * 
    FROM {{ ref('stg_github__events') }} as ghe
    WHERE ghe.type = "PullRequestEvent"
)
SELECT
  pre.id AS id,
  pre.created_at AS created_at,
  pre.repo.id AS repository_id,
  pre.repo.name AS repository_name,
  pre.actor.id AS actor_id,
  pre.actor.login AS actor_login,
  CONCAT("PULL_REQUEST_", UPPER(JSON_VALUE(pre.payload, "$.action"))) as type
FROM pull_request_events AS pre