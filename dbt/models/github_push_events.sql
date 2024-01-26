{#
  Gathers all github events for all github artifacts
#}
{{
  config(
    materialized='incremental'
  )
}}

SELECT
    ghe.created_at as created_at,
    ghe.repo.id as repository_id,
    ghe.repo.name as name,
    JSON_VALUE(ghe.payload, "$.push_id") as push_id,
    JSON_VALUE(ghe.payload, "$.ref") as ref,
    JSON_QUERY_ARRAY(ghe.payload, "$.commits") as commits,
    ARRAY_LENGTH(JSON_QUERY_ARRAY(ghe.payload, "$.commits")) as available_commits_count,
    CAST(JSON_VALUE(ghe.payload, "$.distinct_size") AS INT) as actual_commits_count,
    ghe.actor.id as actor_id,
    ghe.actor.login as actor_login
FROM {{ ref('github_events') }} as ghe