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
    cii.source_id AS event_source_id,
    cii.to_name,
    cii.to_namespace,
    cii.to_type,
    cii.to_source_id,
    cii.from_name,
    cii.from_namespace,
    cii.from_type,
    cii.from_source_id,
    cii.tx_count AS `amount`
  FROM {{ ref('stg_dune__contract_invocation') }} AS cii
  {# a bit of a hack for now to keep this table small for dev and playground #}
  {% if target.name in ['dev', 'playground'] %}
    WHERE cii.time >= TIMESTAMP_SUB(
      CURRENT_TIMESTAMP(),
      INTERVAL {{ env_var("PLAYGROUND_DAYS", '14') }} DAY
    )
  {% endif %}
),

contract_invocation_daily_l2_gas_used AS (
  SELECT
    cii.time,
    "CONTRACT_INVOCATION_DAILY_L2_GAS_USED" AS `event_type`,
    cii.source_id AS event_source_id,
    cii.to_name,
    cii.to_namespace,
    cii.to_type,
    cii.to_source_id,
    cii.from_name,
    cii.from_namespace,
    cii.from_type,
    cii.from_source_id,
    cii.l2_gas AS `amount`
  FROM {{ ref('stg_dune__contract_invocation') }} AS cii
  {% if target.name in ['dev', 'playground'] %}
    WHERE cii.time >= TIMESTAMP_SUB(
      CURRENT_TIMESTAMP(),
      INTERVAL {{ env_var("PLAYGROUND_DAYS", '14') }} DAY
    )
  {% endif %}
),

contract_invocation_daily_l1_gas_used AS (
  SELECT
    cii.time,
    "CONTRACT_INVOCATION_DAILY_L1_GAS_USED" AS `event_type`,
    cii.source_id AS event_source_id,
    cii.to_name,
    cii.to_namespace,
    cii.to_type,
    cii.to_source_id,
    cii.from_name,
    cii.from_namespace,
    cii.from_type,
    cii.from_source_id,
    cii.l1_gas AS `amount`
  FROM {{ ref('stg_dune__contract_invocation') }} AS cii
  {% if target.name in ['dev', 'playground'] %}
    WHERE cii.time >= TIMESTAMP_SUB(
      CURRENT_TIMESTAMP(),
      INTERVAL {{ env_var("PLAYGROUND_DAYS", '14') }} DAY
    )
  {% endif %}
),

github_commits AS (
  SELECT -- noqa: ST06
    gc.created_at AS `time`,
    "COMMIT_CODE" AS `event_type`,
    gc.push_id AS `event_source_id`,
    gc.repository_name AS `to_name`,
    "GITHUB" AS `to_namespace`,
    "GIT_REPOSITORY" AS `to_type`,
    CAST(gc.repository_id AS STRING) AS `to_source_id`,
    COALESCE(gc.actor_login, gc.author_email) AS `from_name`,
    "GITHUB" AS `from_namespace`,
    CASE
      WHEN gc.actor_login IS NOT NULL THEN "GIT_USER"
      ELSE "GIT_EMAIL"
    END AS `from_type`,
    CASE
      WHEN gc.actor_login IS NOT NULL THEN CAST(gc.actor_id AS STRING)
      ELSE gc.author_email
    END AS `from_source_id`,
    CAST(1 AS FLOAT64) AS `amount`
  FROM {{ ref('stg_github__distinct_commits_resolved_mergebot') }} AS gc
),

github_issues AS (
  SELECT -- noqa: ST06
    gi.created_at AS `time`,
    gi.type AS `event_type`,
    CAST(gi.id AS STRING) AS `event_source_id`,
    gi.repository_name AS `to_name`,
    "GITHUB" AS `to_namespace`,
    "GIT_REPOSITORY" AS `to_type`,
    CAST(gi.repository_id AS STRING) AS `to_source_id`,
    gi.actor_login AS `from_name`,
    "GITHUB" AS `from_namespace`,
    "GIT_USER" AS `from_type`,
    CAST(gi.actor_id AS STRING) AS `from_source_id`,
    CAST(1 AS FLOAT64) AS `amount`
  FROM {{ ref('stg_github__issues') }} AS gi
),

github_pull_requests AS (
  SELECT -- noqa: ST06
    gh.created_at AS `time`,
    gh.type AS `event_type`,
    CAST(gh.id AS STRING) AS `event_source_id`,
    gh.repository_name AS `to_name`,
    "GITHUB" AS `to_namespace`,
    "GIT_REPOSITORY" AS `to_type`,
    CAST(gh.repository_id AS STRING) AS `to_source_id`,
    gh.actor_login AS `from_name`,
    "GITHUB" AS `from_namespace`,
    "GIT_USER" AS `from_type`,
    CAST(gh.actor_id AS STRING) AS `from_source_id`,
    CAST(1 AS FLOAT64) AS `amount`
  FROM {{ ref('stg_github__pull_requests') }} AS gh
),

github_pull_request_merge_events AS (
  SELECT -- noqa: ST06
    gh.created_at AS `time`,
    gh.type AS `event_type`,
    CAST(gh.id AS STRING) AS `event_source_id`,
    gh.repository_name AS `to_name`,
    "GITHUB" AS `to_namespace`,
    "GIT_REPOSITORY" AS `to_type`,
    CAST(gh.repository_id AS STRING) AS `to_source_id`,
    gh.actor_login AS `from_name`,
    "GITHUB" AS `from_namespace`,
    "GIT_USER" AS `from_type`,
    CAST(gh.actor_id AS STRING) AS `from_source_id`,
    CAST(1 AS FLOAT64) AS `amount`
  FROM {{ ref('stg_github__pull_request_merge_events') }} AS gh
),

github_stars_and_forks AS (
  SELECT -- noqa: ST06
    gh.created_at AS `time`,
    gh.type AS `event_type`,
    CAST(gh.id AS STRING) AS `event_source_id`,
    gh.repository_name AS `to_name`,
    "GITHUB" AS `to_namespace`,
    "GIT_REPOSITORY" AS `to_type`,
    CAST(gh.repository_id AS STRING) AS `to_source_id`,
    gh.actor_login AS `from_name`,
    "GITHUB" AS `from_namespace`,
    "GIT_USER" AS `from_type`,
    CAST(gh.actor_id AS STRING) AS `from_source_id`,
    CAST(1 AS FLOAT64) AS `amount`
  FROM {{ ref('stg_github__stars_and_forks') }} AS gh
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
UNION ALL
SELECT * FROM github_stars_and_forks
