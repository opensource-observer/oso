MODEL (
  name metrics.stg_github__stars_and_forks,
  kind FULL,
);

with watch_events as (
  select *
  from @oso_source('bigquery.oso.stg_github__events') as ghe
  where ghe.type in ('WatchEvent', 'ForkEvent')
)

select
  we.id as id,
  we.created_at as created_at,
  we.repo.id as repository_id,
  we.repo.name as repository_name,
  we.actor.id as actor_id,
  we.actor.login as actor_login,
  case we.type
    when 'WatchEvent' then 'STARRED'
    when 'ForkEvent' then 'FORKED'
  end as "type"
from watch_events as we
