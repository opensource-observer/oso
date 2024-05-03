{#
  Collects all events into a single table

  SCHEMA
    
  time
  type

  source_id

  to_name
  to_namespace
  to_type
  to_source_id

  from_name
  from_namespace
  from_type
  from_source_id

  amount
#}
{{
  config(
    materialized='table',
    partition_by={
      "field": "time",
      "data_type": "timestamp",
      "granularity": "day",
    }
  )
}}

with contract_invocation_daily_count as (
  select
    cii.time,
    "CONTRACT_INVOCATION_DAILY_COUNT" as `event_type`,
    cii.source_id as event_source_id,
    cii.to_name,
    cii.to_namespace,
    cii.to_type,
    cii.to_source_id,
    cii.from_name,
    cii.from_namespace,
    cii.from_type,
    cii.from_source_id,
    cii.tx_count as `amount`
  from {{ ref('stg_dune__contract_invocation') }} as cii
  {# a bit of a hack for now to keep this table small for dev and playground #}
  {% if target.name in ['dev', 'playground'] %}
    where cii.time >= TIMESTAMP_SUB(
      CURRENT_TIMESTAMP(),
      interval {{ env_var("PLAYGROUND_DAYS", '14') }} day
    )
  {% endif %}
),

contract_invocation_daily_l2_gas_used as (
  select
    cii.time,
    "CONTRACT_INVOCATION_DAILY_L2_GAS_USED" as `event_type`,
    cii.source_id as event_source_id,
    cii.to_name,
    cii.to_namespace,
    cii.to_type,
    cii.to_source_id,
    cii.from_name,
    cii.from_namespace,
    cii.from_type,
    cii.from_source_id,
    cii.l2_gas as `amount`
  from {{ ref('stg_dune__contract_invocation') }} as cii
  {% if target.name in ['dev', 'playground'] %}
    where cii.time >= TIMESTAMP_SUB(
      CURRENT_TIMESTAMP(),
      interval {{ env_var("PLAYGROUND_DAYS", '14') }} day
    )
  {% endif %}
),

contract_invocation_daily_l1_gas_used as (
  select
    cii.time,
    "CONTRACT_INVOCATION_DAILY_L1_GAS_USED" as `event_type`,
    cii.source_id as event_source_id,
    cii.to_name,
    cii.to_namespace,
    cii.to_type,
    cii.to_source_id,
    cii.from_name,
    cii.from_namespace,
    cii.from_type,
    cii.from_source_id,
    cii.l1_gas as `amount`
  from {{ ref('stg_dune__contract_invocation') }} as cii
  {% if target.name in ['dev', 'playground'] %}
    where cii.time >= TIMESTAMP_SUB(
      CURRENT_TIMESTAMP(),
      interval {{ env_var("PLAYGROUND_DAYS", '14') }} day
    )
  {% endif %}
),

github_commits as (
  select -- noqa: ST06
    gc.created_at as `time`,
    "COMMIT_CODE" as `event_type`,
    gc.push_id as `event_source_id`,
    gc.repository_name as `to_name`,
    "GITHUB" as `to_namespace`,
    "GIT_REPOSITORY" as `to_type`,
    CAST(gc.repository_id as STRING) as `to_source_id`,
    COALESCE(gc.actor_login, gc.author_email) as `from_name`,
    "GITHUB" as `from_namespace`,
    case
      when gc.actor_login is not null then "GIT_USER"
      else "GIT_EMAIL"
    end as `from_type`,
    case
      when gc.actor_login is not null then CAST(gc.actor_id as STRING)
      else gc.author_email
    end as `from_source_id`,
    CAST(1 as FLOAT64) as `amount`
  from {{ ref('stg_github__distinct_commits_resolved_mergebot') }} as gc
),

github_issues as (
  select -- noqa: ST06
    gi.created_at as `time`,
    gi.type as `event_type`,
    CAST(gi.id as STRING) as `event_source_id`,
    gi.repository_name as `to_name`,
    "GITHUB" as `to_namespace`,
    "GIT_REPOSITORY" as `to_type`,
    CAST(gi.repository_id as STRING) as `to_source_id`,
    gi.actor_login as `from_name`,
    "GITHUB" as `from_namespace`,
    "GIT_USER" as `from_type`,
    CAST(gi.actor_id as STRING) as `from_source_id`,
    CAST(1 as FLOAT64) as `amount`
  from {{ ref('stg_github__issues') }} as gi
),

github_pull_requests as (
  select -- noqa: ST06
    gh.created_at as `time`,
    gh.type as `event_type`,
    CAST(gh.id as STRING) as `event_source_id`,
    gh.repository_name as `to_name`,
    "GITHUB" as `to_namespace`,
    "GIT_REPOSITORY" as `to_type`,
    CAST(gh.repository_id as STRING) as `to_source_id`,
    gh.actor_login as `from_name`,
    "GITHUB" as `from_namespace`,
    "GIT_USER" as `from_type`,
    CAST(gh.actor_id as STRING) as `from_source_id`,
    CAST(1 as FLOAT64) as `amount`
  from {{ ref('stg_github__pull_requests') }} as gh
),

github_pull_request_merge_events as (
  select -- noqa: ST06
    gh.created_at as `time`,
    gh.type as `event_type`,
    CAST(gh.id as STRING) as `event_source_id`,
    gh.repository_name as `to_name`,
    "GITHUB" as `to_namespace`,
    "GIT_REPOSITORY" as `to_type`,
    CAST(gh.repository_id as STRING) as `to_source_id`,
    gh.actor_login as `from_name`,
    "GITHUB" as `from_namespace`,
    "GIT_USER" as `from_type`,
    CAST(gh.actor_id as STRING) as `from_source_id`,
    CAST(1 as FLOAT64) as `amount`
  from {{ ref('stg_github__pull_request_merge_events') }} as gh
),

github_stars_and_forks as (
  select -- noqa: ST06
    gh.created_at as `time`,
    gh.type as `event_type`,
    CAST(gh.id as STRING) as `event_source_id`,
    gh.repository_name as `to_name`,
    "GITHUB" as `to_namespace`,
    "GIT_REPOSITORY" as `to_type`,
    CAST(gh.repository_id as STRING) as `to_source_id`,
    gh.actor_login as `from_name`,
    "GITHUB" as `from_namespace`,
    "GIT_USER" as `from_type`,
    CAST(gh.actor_id as STRING) as `from_source_id`,
    CAST(1 as FLOAT64) as `amount`
  from {{ ref('stg_github__stars_and_forks') }} as gh
)

select * from contract_invocation_daily_count
union all
select * from contract_invocation_daily_l1_gas_used
union all
select * from contract_invocation_daily_l2_gas_used
union all
select * from github_commits
union all
select * from github_issues
union all
select * from github_pull_requests
union all
select * from github_pull_request_merge_events
union all
select * from github_stars_and_forks
