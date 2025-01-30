MODEL (
  name metrics.stg_github__commits,
  description 'Turns all push events into their commit objects',
  kind FULL,
  dialect trino
);

select
  ghpe.created_at as created_at,
  ghpe.repository_id as repository_id,
  ghpe.repository_name as repository_name,
  ghpe.push_id as push_id,
  ghpe.ref as ref,
  ghpe.actor_id as actor_id,
  ghpe.actor_login as actor_login,
  json_extract_scalar(unnested_ghpe.commit_details, '$.sha') as sha,
  json_extract_scalar(unnested_ghpe.commit_details, '$.author.email') as author_email,
  json_extract_scalar(unnested_ghpe.commit_details, '$.author.name') as author_name,
  CAST(json_extract(unnested_ghpe.commit_details, '$.distinct') as BOOL) as is_distinct,
  json_extract_scalar(unnested_ghpe.commit_details, '$.url') as api_url
from metrics.stg_github__push_events as ghpe
cross join UNNEST(@json_extract_from_array(ghpe.commits, '$')) as unnested_ghpe(commit_details)
