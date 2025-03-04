MODEL (
  name metrics.int_events_aux_issues,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column time,
    batch_size 365,
    batch_concurrency 1
  ),
  start '2015-01-01',
  cron '@daily',
  partitioned_by (DAY("time"), "event_type"),
  grain (time, event_type, event_source, from_artifact_id, to_artifact_id)
);

with github_comments as (
  select -- noqa: ST06
    "event_time" as "time",
    type as event_type,
    CAST(id as STRING) as event_source_id,
    'GITHUB' as event_source,
    SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(1)]
      as to_name,
    SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(0)]
      as to_namespace,
    'REPOSITORY' as to_type,
    CAST(repository_id as STRING) as to_artifact_source_id,
    actor_login as from_name,
    actor_login as from_namespace,
    'GIT_USER' as from_type,
    CAST(actor_id as STRING) as from_artifact_source_id,
    "number" as issue_number,
    created_at,
    merged_at,
    closed_at,
    comments
  from metrics.stg_github__comments
  where event_time between @start_dt and @end_dt
),

github_issues as (
  select -- noqa: ST06
    event_time as "time",
    type as event_type,
    CAST(id as STRING) as event_source_id,
    'GITHUB' as event_source,
    SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(1)]
      as to_name,
    SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(0)]
      as to_namespace,
    'REPOSITORY' as to_type,
    CAST(repository_id as STRING) as to_artifact_source_id,
    actor_login as from_name,
    actor_login as from_namespace,
    'GIT_USER' as from_type,
    CAST(actor_id as STRING) as from_artifact_source_id,
    "number" as issue_number,
    created_at,
    CAST(null as TIMESTAMP) as merged_at,
    closed_at,
    comments
  from metrics.stg_github__issues
  where event_time between @start_dt and @end_dt
),

github_pull_requests as (
  select -- noqa: ST06
    event_time as "time",
    type as event_type,
    CAST(id as STRING) as event_source_id,
    'GITHUB' as event_source,
    SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(1)]
      as to_name,
    SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(0)]
      as to_namespace,
    'REPOSITORY' as to_type,
    CAST(repository_id as STRING) as to_artifact_source_id,
    actor_login as from_name,
    actor_login as from_namespace,
    'GIT_USER' as from_type,
    CAST(actor_id as STRING) as from_artifact_source_id,
    "number" as issue_number,
    created_at,
    merged_at,
    closed_at,
    comments
  from metrics.stg_github__pull_requests
  where event_time between @start_dt and @end_dt
),

github_pull_request_merge_events as (
  select -- noqa: ST06
    created_at as "time",
    type as event_type,
    CAST(id as STRING) as event_source_id,
    'GITHUB' as event_source,
    SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(1)]
      as to_name,
    SPLIT(REPLACE(repository_name, '@', ''), '/')[@array_index(0)]
      as to_namespace,
    'REPOSITORY' as to_type,
    CAST(repository_id as STRING) as to_artifact_source_id,
    actor_login as from_name,
    actor_login as from_namespace,
    'GIT_USER' as from_type,
    CAST(actor_id as STRING) as from_artifact_source_id,
    "number" as issue_number,
    created_at,
    merged_at,
    closed_at,
    comments
  from metrics.stg_github__pull_request_merge_events
  where created_at between @start_dt and @end_dt
),

issue_events as (
  select
    time,
    event_type,
    event_source_id,
    event_source,
    @oso_id(event_source, to_artifact_source_id) as to_artifact_id,
    @oso_id(event_source, from_artifact_source_id) as from_artifact_id,
    issue_number,
    created_at,
    merged_at,
    closed_at,
    comments
  from (
    select * from github_issues
    union all
    select * from github_pull_requests
    union all
    select * from github_pull_request_merge_events
    union all
    select * from github_comments
  )
)

select
  time,
  to_artifact_id,
  from_artifact_id,
  @oso_id(event_source, to_artifact_id, issue_number) as issue_id,
  issue_number,
  created_at,
  merged_at,
  closed_at,
  comments,
  UPPER(event_type) as event_type,
  CAST(event_source_id as STRING) as event_source_id,
  UPPER(event_source) as event_source
from issue_events
