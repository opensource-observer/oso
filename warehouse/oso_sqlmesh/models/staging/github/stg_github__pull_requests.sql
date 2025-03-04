MODEL (
  name metrics.stg_github__pull_requests,
  description 'Turns all watch events into push events',
  kind FULL,
);

with pull_request_events as (
  select *
  from @oso_source('bigquery.oso.stg_github__events') as ghe
  where ghe.type = 'PullRequestEvent'
)

select
  pre.id as id,
  pre.created_at as event_time,
  pre.repo.id as repository_id,
  pre.repo.name as repository_name,
  pre.actor.id as actor_id,
  pre.actor.login as actor_login,
  CONCAT('PULL_REQUEST_', UPPER(json_extract_string(pre.payload, '$.action')))
    as "type",
  json_extract(pre.payload, '$.number')::BIGINT as "number",
  strptime(
    json_extract_string(pre.payload, '$.pull_request.created_at'),
    '%Y-%m-%dT%H:%M:%SZ'
  ) as created_at,
  strptime(
    json_extract_string(pre.payload, '$.pull_request.merged_at'),
    '%Y-%m-%dT%H:%M:%SZ'
  ) as merged_at,
  strptime(
    json_extract_string(pre.payload, '$.pull_request.closed_at'),
    '%Y-%m-%dT%H:%M:%SZ'
  ) as closed_at,
  json_extract_string(
    pre.payload,
    '$.pull_request.state'
  ) as "state",
  json_extract(
    pre.payload,
    '$.pull_request.comments'
  )::DOUBLE as comments
from pull_request_events as pre
