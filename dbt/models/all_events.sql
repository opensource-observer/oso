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
WITH arbitrum_contract_invocation_intermediate AS (
  SELECT 
    CAST(cu.date AS Timestamp) AS `time`,
    TO_BASE64(
      SHA1(
        CONCAT(
          CAST(cu.date AS STRING), 
          cu.address, 
          CASE 
            WHEN cu.user_address IS NULL THEN "" 
            ELSE cu.user_address
          END,
          CASE 
            WHEN cu.safe_address IS NULL THEN "" 
            ELSE cu.safe_address
          END
        ))
    ) as `source_id`,
    cu.address AS `to_name`,
    "ARBITRUM" AS `to_namespace`,
    "CONTRACT_ADDRESS" AS `to_type`,
    cu.address AS `to_source_id`,
    
    CASE
      WHEN cu.safe_address IS NULL THEN cu.user_address
      WHEN cu.user_address IS NULL THEN cu.safe_address
      ELSE "unknown"
    END AS `from_name`,

    "ARBITRUM" AS `from_namespace`,

    CASE
      WHEN cu.safe_address IS NULL THEN "EOA_ADDRESS"
      WHEN cu.user_address IS NULL THEN "SAFE_ADDRESS"
      ELSE "unknown"
    END AS `from_type`,

    CASE
      WHEN cu.safe_address IS NULL THEN cu.user_address
      WHEN cu.user_address IS NULL THEN cu.safe_address
      ELSE "unknown"
    END AS `from_source_id`,

    CAST(cu.l1_gas AS FLOAT64) as `l1_gas`,
    CAST(cu.l2_gas AS FLOAT64) as `l2_gas`,
    CAST(cu.tx_count AS FLOAT64) AS `tx_count`

  FROM `oso-production.opensource_observer.contract_usage` as cu
), arbitrum_contract_invocation_daily_count AS (
  SELECT 
    acii.time,
    "CONTRACT_INVOCATION_DAILY_COUNT" AS `type`,
    acii.source_id,
    acii.to_name,
    acii.to_namespace,
    acii.to_type,
    acii.to_source_id,
    acii.from_name,
    acii.from_namespace,
    acii.from_type,
    acii.from_source_id,
    acii.tx_count as `amount`
  FROM arbitrum_contract_invocation_intermediate AS acii
), arbitrum_contract_invocation_daily_l2_gas_used AS (
  SELECT 
    acii.time,
    "CONTRACT_INVOCATION_DAILY_L2_GAS_USED" AS `type`,
    acii.source_id,
    acii.to_name,
    acii.to_namespace,
    acii.to_type,
    acii.to_source_id,
    acii.from_name,
    acii.from_namespace,
    acii.from_type,
    acii.from_source_id,
    acii.l2_gas as `amount`
  FROM arbitrum_contract_invocation_intermediate AS acii
), arbitrum_contract_invocation_daily_l1_gas_used AS (
  SELECT 
    acii.time,
    "CONTRACT_INVOCATION_DAILY_L1_GAS_USED" AS `type`,
    acii.source_id,
    acii.to_name,
    acii.to_namespace,
    acii.to_type,
    acii.to_source_id,
    acii.from_name,
    acii.from_namespace,
    acii.from_type,
    acii.from_source_id,
    acii.l1_gas as `amount`
  FROM arbitrum_contract_invocation_intermediate AS acii
), github_commits AS (
  SELECT
    gc.created_at as `time`,
    "COMMIT_CODE" as `type`,
    gc.push_id as `source_id`,
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
  FROM {{ ref("github_distinct_commits_resolved_mergebot") }} as gc
), github_issues AS (
  SELECT
    gi.created_at as `time`,
    gi.type as `type`,
    CAST(gi.id AS STRING) as `source_id`,
    gi.repository_name as `to_name`,
    "GITHUB" as `to_namespace`,
    "GIT_REPOSITORY" as `to_type`,
    CAST(gi.repository_id AS STRING) as `to_source_id`,
    gi.actor_login as `from_name`,
    "GITHUB" as `from_namespace`,
    "GIT_USER" as `from_type`,
    CAST(gi.actor_id AS STRING) as `from_source_id`,
    CAST(1 AS FLOAT64) as `amount`
  FROM {{ ref("github_issues") }} as gi
), github_pull_requests AS (
  SELECT
    gh.created_at as `time`,
    gh.type as `type`,
    CAST(gh.id AS STRING) as `source_id`,
    gh.repository_name as `to_name`,
    "GITHUB" as `to_namespace`,
    "GIT_REPOSITORY" as `to_type`,
    CAST(gh.repository_id AS STRING) as `to_source_id`,
    gh.actor_login as `from_name`,
    "GITHUB" as `from_namespace`,
    "GIT_USER" as `from_type`,
    CAST(gh.actor_id AS STRING) as `from_source_id`,
    CAST(1 AS FLOAT64) as `amount`
  FROM {{ ref("github_pull_requests") }} as gh
), github_pull_request_merge_events AS (
  SELECT
    gh.created_at as `time`,
    gh.type as `type`,
    CAST(gh.id AS STRING) as `source_id`,
    gh.repository_name as `to_name`,
    "GITHUB" as `to_namespace`,
    "GIT_REPOSITORY" as `to_type`,
    CAST(gh.repository_id AS STRING) as `to_source_id`,
    gh.actor_login as `from_name`,
    "GITHUB" as `from_namespace`,
    "GIT_USER" as `from_type`,
    CAST(gh.actor_id AS STRING) as `from_source_id`,
    CAST(1 AS FLOAT64) as `amount`
  FROM {{ ref("github_pull_request_merge_events") }} as gh
), github_stars_and_forks AS (
    SELECT
    gh.created_at as `time`,
    gh.type as `type`,
    CAST(gh.id AS STRING) as `source_id`,
    gh.repository_name as `to_name`,
    "GITHUB" as `to_namespace`,
    "GIT_REPOSITORY" as `to_type`,
    CAST(gh.repository_id AS STRING) as `to_source_id`,
    gh.actor_login as `from_name`,
    "GITHUB" as `from_namespace`,
    "GIT_USER" as `from_type`,
    CAST(gh.actor_id AS STRING) as `from_source_id`,
    CAST(1 AS FLOAT64) as `amount`
  FROM {{ ref("github_stars_and_forks") }} as gh
)
SELECT * FROM arbitrum_contract_invocation_daily_count
UNION ALL
SELECT * FROM arbitrum_contract_invocation_daily_l1_gas_used
UNION ALL
SELECT * FROM arbitrum_contract_invocation_daily_l2_gas_used
UNION ALL
SELECT * FROM github_commits
UNION ALL
SELECT * FROM github_issues
UNION ALL
SELECT * FROM github_pull_requests
UNION ALL
SELECT * FROM github_pull_request_merge_events