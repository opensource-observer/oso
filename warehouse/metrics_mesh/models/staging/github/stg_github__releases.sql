MODEL (
  name metrics.stg_github__releases,
  kind FULL,
);

with release_events as (
  select *
  from @oso_source('bigquery.oso.stg_github__events') as ghe
  where ghe.type = 'ReleaseEvent'
)

select
  id as id,
  created_at as created_at,
  repo.id as repository_id,
  repo.name as repository_name,
  actor.id as actor_id,
  actor.login as actor_login,
  'RELEASE_PUBLISHED' as "type"
from release_events
