{#
  Gathers all github events for all github artifacts
#}

SELECT
  ghe.created_at AS created_at,
  ghe.repo.id AS repository_id,
  ghe.repo.name AS repository_name,
  ghe.actor.id AS actor_id,
  ghe.actor.login AS actor_login,
  JSON_VALUE(ghe.payload, "$.push_id") AS push_id,
  JSON_VALUE(ghe.payload, "$.ref") AS ref,
  JSON_QUERY_ARRAY(ghe.payload, "$.commits") AS commits,
  ARRAY_LENGTH(
    JSON_QUERY_ARRAY(ghe.payload, "$.commits")
  ) AS available_commits_count,
  CAST(
    JSON_VALUE(ghe.payload, "$.distinct_size") AS INT
  ) AS actual_commits_count
FROM {{ ref('stg_github__events') }} AS ghe
WHERE ghe.type = "PushEvent"
