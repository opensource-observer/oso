MODEL (
  name oso.stg_github__commits,
  description 'Turns all push events into their commit objects',
  kind FULL,
  dialect trino
);

SELECT
  ghpe.created_at AS created_at,
  ghpe.repository_id AS repository_id,
  ghpe.repository_name AS repository_name,
  ghpe.push_id AS push_id,
  ghpe.ref AS ref,
  ghpe.actor_id AS actor_id,
  ghpe.actor_login AS actor_login,
  JSON_EXTRACT_SCALAR(unnested_ghpe.commit_details, '$.sha') AS sha,
  JSON_EXTRACT_SCALAR(unnested_ghpe.commit_details, '$.author.email') AS author_email,
  JSON_EXTRACT_SCALAR(unnested_ghpe.commit_details, '$.author.name') AS author_name,
  CAST(JSON_EXTRACT(unnested_ghpe.commit_details, '$.distinct') AS BOOLEAN) AS is_distinct,
  JSON_EXTRACT_SCALAR(unnested_ghpe.commit_details, '$.url') AS api_url
FROM oso.stg_github__push_events AS ghpe
CROSS JOIN UNNEST(@json_extract_from_array(ghpe.commits, '$')) AS unnested_ghpe(commit_details)