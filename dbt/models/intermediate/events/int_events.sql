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

WITH contract_invocation_daily_count AS (
  SELECT 
    cii.time,
    "CONTRACT_INVOCATION_DAILY_COUNT" AS `event_type`,
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
  FROM {{ ref('stg_dune__contract_invocation') }} AS cii
  {# a bit of a hack for now to keep this table small for dev and playground #}
  {% if target.name in ['dev', 'playground'] %}
  WHERE cii.time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {{ env_var("PLAYGROUND_DAYS", '14') }} DAY)
  {% endif %}
), contract_invocation_daily_l2_gas_used AS (
  SELECT 
    cii.time,
    "CONTRACT_INVOCATION_DAILY_L2_GAS_USED" AS `event_type`,
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
  FROM {{ ref('stg_dune__contract_invocation') }} AS cii
  {% if target.name in ['dev', 'playground'] %}
  WHERE cii.time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {{ env_var("PLAYGROUND_DAYS", '14') }} DAY)
  {% endif %}
), contract_invocation_daily_l1_gas_used AS (
  SELECT 
    cii.time,
    "CONTRACT_INVOCATION_DAILY_L1_GAS_USED" AS `event_type`,
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
  FROM {{ ref('stg_dune__contract_invocation') }} AS cii
  {% if target.name in ['dev', 'playground'] %}
  WHERE cii.time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {{ env_var("PLAYGROUND_DAYS", '14') }} DAY)
  {% endif %}
), github_commits AS (
  SELECT
    gc.created_at as `time`,
    "COMMIT_CODE" as `event_type`,
    gc.push_id as `event_source_id`,
    gc.repository_name as `to_name`,
    "GITHUB" as `to_namespace`,
    "GIT_REPOSITORY" as `to_type`,
    CAST(gc.repository_id AS STRING) as `to_source_id`,
    CASE
      WHEN gc.actor_login IS NOT NULL THEN gc.actor_login
      ELSE gc.author_email
    END as `from_name`,
    "GITHUB" as `from_namespace`,
    CASE
      WHEN gc.actor_login IS NOT NULL THEN "GIT_USER"
      ELSE "GIT_EMAIL"
    END as `from_type`,
    CASE
      WHEN gc.actor_login IS NOT NULL THEN CAST(gc.actor_id AS STRING)
      ELSE gc.author_email
    END as `from_source_id`,
    CAST(1 AS FLOAT64) as `amount`
  FROM {{ ref('stg_github__distinct_commits_resolved_mergebot') }} as gc
), github_issues AS (
  SELECT
    gi.created_at as `time`,
    gi.type as `event_type`,
    CAST(gi.id AS STRING) as `event_source_id`,
    gi.repository_name as `to_name`,
    "GITHUB" as `to_namespace`,
    "GIT_REPOSITORY" as `to_type`,
    CAST(gi.repository_id AS STRING) as `to_source_id`,
    gi.actor_login as `from_name`,
    "GITHUB" as `from_namespace`,
    "GIT_USER" as `from_type`,
    CAST(gi.actor_id AS STRING) as `from_source_id`,
    CAST(1 AS FLOAT64) as `amount`
  FROM {{ ref('stg_github__issues') }} as gi
), github_pull_requests AS (
  SELECT
    gh.created_at as `time`,
    gh.type as `event_type`,
    CAST(gh.id AS STRING) as `event_source_id`,
    gh.repository_name as `to_name`,
    "GITHUB" as `to_namespace`,
    "GIT_REPOSITORY" as `to_type`,
    CAST(gh.repository_id AS STRING) as `to_source_id`,
    gh.actor_login as `from_name`,
    "GITHUB" as `from_namespace`,
    "GIT_USER" as `from_type`,
    CAST(gh.actor_id AS STRING) as `from_source_id`,
    CAST(1 AS FLOAT64) as `amount`
  FROM {{ ref('stg_github__pull_requests') }} as gh
), github_pull_request_merge_events AS (
  SELECT
    gh.created_at as `time`,
    gh.type as `event_type`,
    CAST(gh.id AS STRING) as `event_source_id`,
    gh.repository_name as `to_name`,
    "GITHUB" as `to_namespace`,
    "GIT_REPOSITORY" as `to_type`,
    CAST(gh.repository_id AS STRING) as `to_source_id`,
    gh.actor_login as `from_name`,
    "GITHUB" as `from_namespace`,
    "GIT_USER" as `from_type`,
    CAST(gh.actor_id AS STRING) as `from_source_id`,
    CAST(1 AS FLOAT64) as `amount`
  FROM {{ ref('stg_github__pull_request_merge_events') }} as gh
), github_stars_and_forks AS (
    SELECT
    gh.created_at as `time`,
    gh.type as `event_type`,
    CAST(gh.id AS STRING) as `event_source_id`,
    gh.repository_name as `to_name`,
    "GITHUB" as `to_namespace`,
    "GIT_REPOSITORY" as `to_type`,
    CAST(gh.repository_id AS STRING) as `to_source_id`,
    gh.actor_login as `from_name`,
    "GITHUB" as `from_namespace`,
    "GIT_USER" as `from_type`,
    CAST(gh.actor_id AS STRING) as `from_source_id`,
    CAST(1 AS FLOAT64) as `amount`
  FROM {{ ref('stg_github__stars_and_forks') }} as gh
)
SELECT * FROM contract_invocation_daily_count
UNION ALL
SELECT * FROM contract_invocation_daily_l1_gas_used
UNION ALL
SELECT * FROM contract_invocation_daily_l2_gas_used
UNION ALL
SELECT * FROM github_commits
UNION ALL
SELECT * FROM github_issues
UNION ALL
SELECT * FROM github_pull_requests
UNION ALL
SELECT * FROM github_pull_request_merge_events