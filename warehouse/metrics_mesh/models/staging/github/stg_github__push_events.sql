MODEL (
  name metrics.stg_github__push_events,
  description 'Gathers all github events for all github artifacts',
  kind FULL,
);

select
  ghe.created_at as created_at,
  ghe.repo.id as repository_id,
  ghe.repo.name as repository_name,
  ghe.actor.id as actor_id,
  ghe.actor.login as actor_login,
  json_extract_string(ghe.payload, '$.push_id') as push_id,
  json_extract_string(ghe.payload, '$.ref') as ref,
  json_extract(ghe.payload, '$.commits')::JSON[] as commits,
  json_array_length(ghe.payload, '$.commits') as available_commits_count,
  CAST(
    json_extract(ghe.payload, '$.distinct_size') as INT
  ) as actual_commits_count
from @oso_source('bigquery.oso.stg_github__events') as ghe
where ghe.type = 'PushEvent'
