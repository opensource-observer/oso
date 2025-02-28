{{
  config(
    materialized='table',
    partition_by={
      "field": "time",
      "data_type": "timestamp",
      "granularity": "day",
    },
    meta={
      'sync_to_db': False
    }
  )
}}

with github_commits as (
  select -- noqa: ST06
    created_at as `time`,
    "COMMIT_CODE" as event_type,
    CAST(push_id as STRING) as event_source_id,
    "GITHUB" as event_source,
    SPLIT(REPLACE(repository_name, "@", ""), "/")[SAFE_OFFSET(1)]
      as to_name,
    SPLIT(REPLACE(repository_name, "@", ""), "/")[SAFE_OFFSET(0)]
      as to_namespace,
    "REPOSITORY" as to_type,
    CAST(repository_id as STRING) as to_artifact_source_id,
    COALESCE(actor_login, author_email) as from_name,
    COALESCE(actor_login, author_email) as from_namespace,
    case
      when actor_login is not null then "GIT_USER"
      else "GIT_EMAIL"
    end as from_type,
    case
      when actor_login is not null then CAST(actor_id as STRING)
      else author_email
    end as from_artifact_source_id,
    CAST(1 as FLOAT64) as amount
  from {{ ref('stg_github__distinct_commits_resolved_mergebot') }}
),

github_releases as (
  select -- noqa: ST06
    created_at as `time`,
    type as event_type,
    CAST(id as STRING) as event_source_id,
    "GITHUB" as event_source,
    SPLIT(REPLACE(repository_name, "@", ""), "/")[SAFE_OFFSET(1)]
      as to_name,
    SPLIT(REPLACE(repository_name, "@", ""), "/")[SAFE_OFFSET(0)]
      as to_namespace,
    "REPOSITORY" as to_type,
    CAST(repository_id as STRING) as to_artifact_source_id,
    actor_login as from_name,
    actor_login as from_namespace,
    "GIT_USER" as from_type,
    CAST(actor_id as STRING) as from_artifact_source_id,
    CAST(1 as FLOAT64) as amount
  from {{ ref('stg_github__releases') }}
),

github_comments as (
  select -- noqa: ST06
    event_time as `time`,
    type as event_type,
    CAST(id as STRING) as event_source_id,
    "GITHUB" as event_source,
    SPLIT(REPLACE(repository_name, "@", ""), "/")[SAFE_OFFSET(1)]
      as to_name,
    SPLIT(REPLACE(repository_name, "@", ""), "/")[SAFE_OFFSET(0)]
      as to_namespace,
    "REPOSITORY" as to_type,
    CAST(repository_id as STRING) as to_artifact_source_id,
    actor_login as from_name,
    actor_login as from_namespace,
    "GIT_USER" as from_type,
    CAST(actor_id as STRING) as from_artifact_source_id,
    CAST(1 as FLOAT64) as amount
  from {{ ref('stg_github__comments') }}
),

github_issues as (
  select -- noqa: ST06
    event_time as `time`,
    type as event_type,
    CAST(id as STRING) as event_source_id,
    "GITHUB" as event_source,
    SPLIT(REPLACE(repository_name, "@", ""), "/")[SAFE_OFFSET(1)]
      as to_name,
    SPLIT(REPLACE(repository_name, "@", ""), "/")[SAFE_OFFSET(0)]
      as to_namespace,
    "REPOSITORY" as to_type,
    CAST(repository_id as STRING) as to_artifact_source_id,
    actor_login as from_name,
    actor_login as from_namespace,
    "GIT_USER" as from_type,
    CAST(actor_id as STRING) as from_artifact_source_id,
    CAST(1 as FLOAT64) as amount
  from {{ ref('stg_github__issues') }}
),

github_pull_requests as (
  select -- noqa: ST06
    event_time as `time`,
    type as event_type,
    CAST(id as STRING) as event_source_id,
    "GITHUB" as event_source,
    SPLIT(REPLACE(repository_name, "@", ""), "/")[SAFE_OFFSET(1)]
      as to_name,
    SPLIT(REPLACE(repository_name, "@", ""), "/")[SAFE_OFFSET(0)]
      as to_namespace,
    "REPOSITORY" as to_type,
    CAST(repository_id as STRING) as to_artifact_source_id,
    actor_login as from_name,
    actor_login as from_namespace,
    "GIT_USER" as from_type,
    CAST(actor_id as STRING) as from_artifact_source_id,
    CAST(1 as FLOAT64) as amount
  from {{ ref('stg_github__pull_requests') }}
),

github_pull_request_merge_events as (
  select -- noqa: ST06
    event_time as `time`,
    type as event_type,
    CAST(id as STRING) as event_source_id,
    "GITHUB" as event_source,
    SPLIT(REPLACE(repository_name, "@", ""), "/")[SAFE_OFFSET(1)]
      as to_name,
    SPLIT(REPLACE(repository_name, "@", ""), "/")[SAFE_OFFSET(0)]
      as to_namespace,
    "REPOSITORY" as to_type,
    CAST(repository_id as STRING) as to_artifact_source_id,
    actor_login as from_name,
    actor_login as from_namespace,
    "GIT_USER" as from_type,
    CAST(actor_id as STRING) as from_artifact_source_id,
    CAST(1 as FLOAT64) as amount
  from {{ ref('stg_github__pull_request_merge_events') }}
),

github_stars_and_forks as (
  select -- noqa: ST06
    created_at as `time`,
    type as event_type,
    CAST(id as STRING) as event_source_id,
    "GITHUB" as event_source,
    SPLIT(REPLACE(repository_name, "@", ""), "/")[SAFE_OFFSET(1)]
      as to_name,
    SPLIT(REPLACE(repository_name, "@", ""), "/")[SAFE_OFFSET(0)]
      as to_namespace,
    "REPOSITORY" as to_type,
    CAST(repository_id as STRING) as to_artifact_source_id,
    actor_login as from_name,
    actor_login as from_namespace,
    "GIT_USER" as from_type,
    CAST(actor_id as STRING) as from_artifact_source_id,
    CAST(1 as FLOAT64) as amount
  from {{ ref('stg_github__stars_and_forks') }}
),

all_events as (
  select
    time,
    event_type,
    event_source_id,
    event_source,
    {{ oso_id("event_source", "to_artifact_source_id") }} as to_artifact_id,
    to_name as to_artifact_name,
    to_namespace as to_artifact_namespace,
    to_type as to_artifact_type,
    to_artifact_source_id,
    {{ oso_id("event_source", "from_artifact_source_id") }} as from_artifact_id,
    from_name as from_artifact_name,
    from_namespace as from_artifact_namespace,
    from_type as from_artifact_type,
    from_artifact_source_id,
    amount
  from (
    select * from github_commits
    union all
    select * from github_issues
    union all
    select * from github_pull_requests
    union all
    select * from github_pull_request_merge_events
    union all
    select * from github_releases
    union all
    select * from github_stars_and_forks
    union all
    select * from github_comments
  )
)

select
  time,
  to_artifact_id,
  from_artifact_id,
  UPPER(event_type) as event_type,
  CAST(event_source_id as STRING) as event_source_id,
  UPPER(event_source) as event_source,
  LOWER(to_artifact_name) as to_artifact_name,
  LOWER(to_artifact_namespace) as to_artifact_namespace,
  UPPER(to_artifact_type) as to_artifact_type,
  LOWER(to_artifact_source_id) as to_artifact_source_id,
  LOWER(from_artifact_name) as from_artifact_name,
  LOWER(from_artifact_namespace) as from_artifact_namespace,
  UPPER(from_artifact_type) as from_artifact_type,
  LOWER(from_artifact_source_id) as from_artifact_source_id,
  CAST(amount as FLOAT64) as amount
from all_events
