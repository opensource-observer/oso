with pr_events as (
  select
    `number`,
    `type`,
    actor_id,
    event_time as `time`,
    LOWER(actor_login) as actor_login,
    LOWER(repository_name) as repository_name,
    CAST(repository_id as STRING) as to_artifact_source_id
  from {{ ref('stg_github__pull_requests') }}
  where `type` = 'PULL_REQUEST_OPENED'
),

merge_events as (
  select
    `number`,
    `type`,
    actor_id,
    created_at as `time`,
    LOWER(actor_login) as actor_login,
    LOWER(repository_name) as repository_name,
    CAST(repository_id as STRING) as to_artifact_source_id
  from {{ ref('stg_github__pull_request_merge_events') }}
),

issue_events as (
  select
    `number`,
    `type`,
    actor_id,
    event_time as `time`,
    LOWER(actor_login) as actor_login,
    LOWER(repository_name) as repository_name,
    CAST(repository_id as STRING) as to_artifact_source_id
  from {{ ref('stg_github__issues') }}
),

comment_events as (
  select
    `number`,
    `type`,
    actor_id,
    event_time as `time`,
    LOWER(actor_login) as actor_login,
    LOWER(repository_name) as repository_name,
    CAST(repository_id as STRING) as to_artifact_source_id
  from {{ ref('stg_github__comments') }}
),

all_events as (
  select
    `number`,
    `type`,
    actor_login,
    repository_name,
    actor_id,
    to_artifact_source_id,
    `time`,
    'GITHUB' as event_source
  from pr_events
  union all
  select
    `number`,
    `type`,
    actor_login,
    repository_name,
    actor_id,
    to_artifact_source_id,
    `time`,
    'GITHUB' as event_source
  from merge_events
  union all
  select
    `number`,
    `type`,
    actor_login,
    repository_name,
    actor_id,
    to_artifact_source_id,
    `time`,
    'GITHUB' as event_source
  from issue_events
  union all
  select
    `number`,
    `type`,
    actor_login,
    repository_name,
    actor_id,
    to_artifact_source_id,
    `time`,
    'GITHUB' as event_source
  from comment_events
)

select
  'GITHUB' as event_source,
  `time`,
  `number`,
  `type`,
  actor_login,
  repository_name,
  actor_id,
  to_artifact_source_id,
  {{ oso_id("event_source", "to_artifact_source_id") }} as to_artifact_id
from all_events
where actor_login not like '%[bot]'
