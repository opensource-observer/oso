MODEL (
  name metrics.stg_github__pull_request_merge_events,
  kind FULL,
);

with pull_request_events as (
  select *
  from @oso_source('bigquery.oso.stg_github__events') as ghe
  where ghe.type = 'PullRequestEvent'
)

select distinct
  pre.repo.id as repository_id,
  pre.repo.name as repository_name,
  'PULL_REQUEST_MERGED' as "type",
  json_extract(pre.payload, '$.pull_request.id')::VARCHAR as id,
  strptime(
    json_extract_string(pre.payload, '$.pull_request.merged_at'),
    '%Y-%m-%dT%H:%M:%SZ'
  ) as event_time,
  strptime(
    json_extract_string(pre.payload, '$.pull_request.merged_at'),
    '%Y-%m-%dT%H:%M:%SZ'
  ) as merged_at,
  strptime(
    json_extract_string(pre.payload, '$.pull_request.created_at'),
    '%Y-%m-%dT%H:%M:%SZ'
  ) as created_at,
  strptime(
    json_extract_string(pre.payload, '$.pull_request.closed_at'),
    '%Y-%m-%dT%H:%M:%SZ'
  ) as closed_at,
  CAST(json_extract(pre.payload, '$.pull_request.user.id') as INTEGER)
    as actor_id,
  json_extract_string(
    pre.payload, '$.pull_request.user.login'
  ) as actor_login,
  json_extract_string(
    pre.payload, '$.pull_request.state'
  ) as state,
  json_extract_string(
    pre.payload, '$.pull_request.merge_commit_sha'
  ) as merge_commit_sha,
  json_extract(
    pre.payload, '$.pull_request.changed_files'
  )::INT as changed_files,
  json_extract(
    pre.payload, '$.pull_request.additions'
  )::INT as additions,
  json_extract(
    pre.payload, '$.pull_request.deletions'
  )::INT as deletions,
  json_extract(
    pre.payload, '$.pull_request.review_comments'
  )::DOUBLE as review_comments,
  json_extract(
    pre.payload, '$.pull_request.comments'
  )::DOUBLE as comments,
  json_extract_string(
    pre.payload, '$.pull_request.author_association'
  ) as author_association,
  json_extract(pre.payload, '$.number')::BIGINT as "number"
from pull_request_events as pre
where
  json_extract_string(pre.payload, '$.pull_request.merged_at') is not null
  and json_extract_string(pre.payload, '$.action') = 'closed'
