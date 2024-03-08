{#
  Turns all push events into their commit objects
#}

SELECT
  ghpe.created_at AS created_at,
  ghpe.repository_id AS repository_id,
  ghpe.repository_name AS repository_name,
  ghpe.push_id AS push_id,
  ghpe.ref AS ref,
  ghpe.actor_id AS actor_id,
  ghpe.actor_login AS actor_login,
  JSON_VALUE(commit_details, "$.sha") AS sha,
  JSON_VALUE(commit_details, "$.author.email") AS author_email,
  JSON_VALUE(commit_details, "$.author.name") AS author_name,
  CAST(JSON_VALUE(commit_details, "$.distinct") AS BOOL) AS is_distinct,
  JSON_VALUE(commit_details, "$.url") AS api_url
FROM {{ ref('stg_github__push_events') }} AS ghpe
CROSS JOIN UNNEST(ghpe.commits) AS commit_details
