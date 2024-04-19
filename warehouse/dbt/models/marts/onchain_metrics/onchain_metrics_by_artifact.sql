{#
Summary onchain metrics for a project:
  - artifact_id: The unique identifier for the artifact
  - network: The network the artifact is deployed on
  - artifact_name: The name of the artifact
  - num_contracts: The number of contracts in the artifact
  - first_txn_date: The date of the first transaction to the artifact
  - total_txns: The total number of transactions to the artifact
  - total_l2_gas: The total L2 gas used by the artifact
  - total_users: The number of unique users interacting with the artifact
  - txns_6_months: The total number of transactions to the artifact in the last 6 months
  - l2_gas_6_months: The total L2 gas used by the artifact in the last 6 months
  - users_6_months: The number of unique users interacting with the artifact in the last 6 months
  - new_users: The number of users interacting with the artifact for the first time in the last 3 months
  - active_users: The number of active users interacting with the artifact in the last 3 months
  - high_frequency_users: The number of users who have made 1000+ transactions with the artifact in the last 3 months
  - more_active_users: The number of users who have made 10-999 transactions with the artifact in the last 3 months
  - less_active_users: The number of users who have made 1-9 transactions with the artifact in the last 3 months
  - multi_project_users: The number of users who have interacted with 3+ artifacts in the last 3 months
#}
{{ 
  config(meta = {
    'sync_to_cloudsql': True
  }) 
}}


WITH txns AS (
  SELECT
    a.artifact_id,
    a.artifact_name,
    c.to_namespace AS onchain_network,
    c.from_source_id AS from_id,
    c.l2_gas,
    c.tx_count,
    DATE(TIMESTAMP_TRUNC(c.time, MONTH)) AS bucket_month
  FROM {{ ref('stg_dune__contract_invocation') }} AS c
  INNER JOIN {{ ref('stg_ossd__artifacts_by_project') }} AS a
    ON c.to_source_id = a.artifact_source_id
),

metrics_all_time AS (
  SELECT
    artifact_id,
    artifact_name,
    onchain_network,
    COUNT(DISTINCT from_id) AS total_users,
    SUM(l2_gas) AS total_l2_gas,
    SUM(tx_count) AS total_txns
  FROM txns
  GROUP BY artifact_id, artifact_name, onchain_network
),

metrics_6_months AS (
  SELECT
    artifact_id,
    artifact_name,
    onchain_network,
    COUNT(DISTINCT from_id) AS users_6_months,
    SUM(l2_gas) AS l2_gas_6_months,
    SUM(tx_count) AS txns_6_months
  FROM txns
  WHERE bucket_month >= DATE_ADD(CURRENT_DATE(), INTERVAL -6 MONTH)
  GROUP BY artifact_id, artifact_name, onchain_network
),

new_users AS (
  SELECT
    artifact_id,
    artifact_name,
    onchain_network,
    SUM(is_new_user) AS new_user_count
  FROM (
    SELECT
      artifact_id,
      artifact_name,
      onchain_network,
      from_id,
      CASE
        WHEN MIN(bucket_month) >= DATE_ADD(CURRENT_DATE(), INTERVAL -3 MONTH) THEN 1
      END AS is_new_user
    FROM txns
    GROUP BY artifact_id, artifact_name, onchain_network, from_id
  )
  GROUP BY artifact_id, artifact_name, onchain_network
),

user_segments AS (
  SELECT
    artifact_id,
    artifact_name,
    onchain_network,
    COUNT(DISTINCT CASE WHEN user_segment = 'HIGH_FREQUENCY_USER' THEN from_id END) AS high_frequency_users,
    COUNT(DISTINCT CASE WHEN user_segment = 'MORE_ACTIVE_USER' THEN from_id END) AS more_active_users,
    COUNT(DISTINCT CASE WHEN user_segment = 'LESS_ACTIVE_USER' THEN from_id END) AS less_active_users,
    COUNT(DISTINCT CASE WHEN projects_transacted_on >= 3 THEN from_id END) AS multi_project_users
  FROM (
    SELECT
      uta.artifact_id,
      uta.artifact_name,
      uta.onchain_network,
      uta.from_id,
      mpu.projects_transacted_on,
      CASE
        WHEN uta.total_tx_count >= 1000 THEN 'HIGH_FREQUENCY_USER'
        WHEN uta.total_tx_count >= 10 THEN 'MORE_ACTIVE_USER'
        ELSE 'LESS_ACTIVE_USER'
      END AS user_segment
    FROM (
      SELECT
        artifact_id,
        artifact_name,
        onchain_network,
        from_id,
        SUM(tx_count) AS total_tx_count
      FROM txns
      WHERE bucket_month >= DATE_ADD(CURRENT_DATE(), INTERVAL -3 MONTH)
      GROUP BY artifact_id, artifact_name, onchain_network, from_id
    ) AS uta
    INNER JOIN (
      SELECT
        onchain_network,
        from_id,
        COUNT(DISTINCT artifact_id) AS projects_transacted_on
      FROM txns
      WHERE bucket_month >= DATE_ADD(CURRENT_DATE(), INTERVAL -3 MONTH)
      GROUP BY onchain_network, from_id
    ) AS mpu ON uta.from_id = mpu.from_id
  ) AS user_txns_aggregated
  GROUP BY artifact_id, artifact_name, onchain_network
),

contracts AS (
  SELECT
    artifact_id,
    artifact_namespace AS onchain_network,
    COUNT(artifact_source_id) AS num_contracts
  FROM {{ ref('stg_ossd__artifacts_by_project') }}
  GROUP BY artifact_id, artifact_namespace
),

project_by_network AS (
  SELECT
    a.artifact_id,
    a.artifact_namespace AS onchain_network,
    a.artifact_name
  FROM {{ ref('stg_ossd__artifacts_by_project') }} AS a
)

SELECT
  p.artifact_id,
  p.onchain_network AS network,
  p.artifact_name,
  c.num_contracts,
  ma.total_users,
  ma.total_l2_gas,
  ma.total_txns,
  m6.users_6_months,
  m6.l2_gas_6_months,
  m6.txns_6_months,
  nu.new_user_count,
  us.high_frequency_users,
  us.more_active_users,
  us.less_active_users,
  us.multi_project_users,
  (us.high_frequency_users + us.more_active_users + us.less_active_users) AS active_users
FROM project_by_network AS p
LEFT JOIN metrics_all_time AS ma ON p.artifact_id = ma.artifact_id AND p.onchain_network = ma.onchain_network
LEFT JOIN metrics_6_months AS m6 ON p.artifact_id = m6.artifact_id AND p.onchain_network = m6.onchain_network
LEFT JOIN new_users AS nu ON p.artifact_id = nu.artifact_id AND p.onchain_network = nu.onchain_network
LEFT JOIN user_segments AS us ON p.artifact_id = us.artifact_id AND p.onchain_network = us.onchain_network
LEFT JOIN contracts AS c ON p.artifact_id = c.artifact_id AND p.onchain_network = c.onchain_network;
