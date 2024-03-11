{# 
  Summary onchain metrics for a project:
    - project_id: The unique identifier for the project
    - network: The network the project is deployed on
    - num_contracts: The number of contracts in the project
    - first_txn_date: The date of the first transaction to the project
    - total_txns: The total number of transactions to the project
    - total_l2_gas: The total L2 gas used by the project
    - total_users: The number of unique users interacting with the project    
    - txns_6_months: The total number of transactions to the project in the last 6 months
    - l2_gas_6_months: The total L2 gas used by the project in the last 6 months
    - users_6_months: The number of unique users interacting with the project in the last 6 months
    - new_users: The number of users interacting with the project for the first time in the last 3 months
    - active_users: The number of active users interacting with the project in the last 3 months
    - high_frequency_users: The number of users who have made 1000+ transactions with the project in the last 3 months
    - more_active_users: The number of users who have made 10-999 transactions with the project in the last 3 months
    - less_active_users: The number of users who have made 1-9 transactions with the project in the last 3 months
    - multi_project_users: The number of users who have interacted with 3+ projects in the last 3 months
#}

-- CTE for grabbing the onchain transaction data we care about
WITH txns AS (
  SELECT
    a.project_id,
    c.to_namespace AS onchain_network,
    c.from_source_id AS from_id,
    c.l2_gas,
    c.tx_count,
    DATE(TIMESTAMP_TRUNC(c.time, MONTH)) AS bucket_month
  FROM {{ ref('stg_dune__contract_invocation') }} AS c
  INNER JOIN {{ ref('stg_ossd__artifacts_by_project') }} AS a
    ON c.to_source_id = a.artifact_source_id
),

-- CTEs for calculating all time and 6 month project metrics across all 
-- contracts
metrics_all_time AS (
  SELECT
    project_id,
    onchain_network,
    MIN(bucket_month) AS first_txn_date,
    COUNT(DISTINCT from_id) AS total_users,
    SUM(l2_gas) AS total_l2_gas,
    SUM(tx_count) AS total_txns
  FROM txns
  GROUP BY project_id, onchain_network
),

metrics_6_months AS (
  SELECT
    project_id,
    onchain_network,
    COUNT(DISTINCT from_id) AS users_6_months,
    SUM(l2_gas) AS l2_gas_6_months,
    SUM(tx_count) AS txns_6_months
  FROM txns
  WHERE bucket_month >= DATE_ADD(CURRENT_DATE(), INTERVAL -6 MONTH)
  GROUP BY project_id, onchain_network
),

-- CTE for identifying new users to the project in the last 3 months
new_users AS (
  SELECT
    project_id,
    onchain_network,
    SUM(is_new_user) AS new_user_count
  FROM (
    SELECT
      project_id,
      onchain_network,
      from_id,
      CASE
        WHEN
          MIN(bucket_month) >= DATE_ADD(CURRENT_DATE(), INTERVAL -3 MONTH)
          THEN
            1
      END AS is_new_user
    FROM txns
    GROUP BY project_id, onchain_network, from_id
  )
  GROUP BY project_id, onchain_network
),

-- CTEs for segmenting different types of active users based on txn volume
user_txns_aggregated AS (
  SELECT
    project_id,
    onchain_network,
    from_id,
    SUM(tx_count) AS total_tx_count
  FROM txns
  WHERE bucket_month >= DATE_ADD(CURRENT_DATE(), INTERVAL -3 MONTH)
  GROUP BY project_id, onchain_network, from_id
),

multi_project_users AS (
  SELECT
    onchain_network,
    from_id,
    COUNT(DISTINCT project_id) AS projects_transacted_on
  FROM user_txns_aggregated
  GROUP BY onchain_network, from_id
),

user_segments AS (
  SELECT
    project_id,
    onchain_network,
    COUNT(DISTINCT CASE
      WHEN user_segment = 'HIGH_FREQUENCY_USER' THEN from_id
    END) AS high_frequency_users,
    COUNT(DISTINCT CASE
      WHEN user_segment = 'MORE_ACTIVE_USER' THEN from_id
    END) AS more_active_users,
    COUNT(DISTINCT CASE
      WHEN user_segment = 'LESS_ACTIVE_USER' THEN from_id
    END) AS less_active_users,
    COUNT(DISTINCT CASE
      WHEN projects_transacted_on >= 3 THEN from_id
    END) AS multi_project_users
  FROM (
    SELECT
      uta.project_id,
      uta.onchain_network,
      uta.from_id,
      mpu.projects_transacted_on,
      CASE
        WHEN uta.total_tx_count >= 1000 THEN 'HIGH_FREQUENCY_USER'
        WHEN uta.total_tx_count >= 10 THEN 'MORE_ACTIVE_USER'
        ELSE 'LESS_ACTIVE_USER'
      END AS user_segment
    FROM user_txns_aggregated AS uta
    INNER JOIN multi_project_users AS mpu
      ON uta.from_id = mpu.from_id
  )
  GROUP BY project_id, onchain_network
),

-- CTE to count the number of contracts deployed by a project
contracts AS (
  SELECT
    project_id,
    artifact_namespace AS onchain_network,
    COUNT(artifact_source_id) AS num_contracts
  FROM {{ ref('stg_ossd__artifacts_by_project') }}
  GROUP BY project_id, onchain_network
),

project_by_network AS (
  SELECT
    p.project_id,
    ctx.onchain_network,
    p.project_name
  FROM {{ ref('projects') }} AS p
  INNER JOIN contracts AS ctx
    ON p.project_id = ctx.project_id
)

-- Final query to join all the metrics together
SELECT
  p.project_id,
  p.onchain_network AS network,
  p.project_name,
  -- TODO: add deployers owned by project
  c.num_contracts,
  ma.first_txn_date,
  ma.total_txns,
  ma.total_l2_gas,
  ma.total_users,
  m6.txns_6_months,
  m6.l2_gas_6_months,
  m6.users_6_months,
  nu.new_user_count,
  us.high_frequency_users,
  us.more_active_users,
  us.less_active_users,
  us.multi_project_users,
  (
    us.high_frequency_users + us.more_active_users + us.less_active_users
  ) AS active_users
FROM project_by_network AS p
LEFT JOIN metrics_all_time AS ma
  ON
    p.project_id = ma.project_id
    AND p.onchain_network = ma.onchain_network
LEFT JOIN metrics_6_months AS m6
  ON
    p.project_id = m6.project_id
    AND p.onchain_network = m6.onchain_network
LEFT JOIN new_users AS nu
  ON
    p.project_id = nu.project_id
    AND p.onchain_network = nu.onchain_network
LEFT JOIN user_segments AS us
  ON
    p.project_id = us.project_id
    AND p.onchain_network = us.onchain_network
LEFT JOIN contracts AS c
  ON
    p.project_id = c.project_id
    AND p.onchain_network = c.onchain_network
