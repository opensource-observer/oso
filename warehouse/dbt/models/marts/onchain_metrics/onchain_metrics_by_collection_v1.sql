{# 
  Arbitrum Onchain Metrics
  Summary onchain metrics for a collection:
    - num_projects: The number of projects in the collection
    - num_contracts: The number of contracts in the collection
    - first_txn_date: The date of the first transaction to the collection
    - total_txns: The total number of transactions to the collection
    - total_l2_gas: The total L2 gas used by the collection
    - total_users: The number of unique users interacting with the collection    
    - txns_6_months: The total number of transactions to the collection in the last 6 months
    - l2_gas_6_months: The total L2 gas used by the collection in the last 6 months
    - users_6_months: The number of unique users interacting with the collection in the last 6 months
    - new_users: The number of users interacting with the collection for the first time in the last 3 months
    - active_users: The number of active users interacting with the collection in the last 3 months
    - high_frequency_users: The number of users who have made 1000+ transactions with the collection in the last 3 months
    - more_active_users: The number of users who have made 10-999 transactions with the collection in the last 3 months
    - less_active_users: The number of users who have made 1-9 transactions with the collection in the last 3 months
    - multi_project_users: The number of users who have interacted with 3+ projects in the last 3 months
#}
{{ 
  config(meta = {
    'sync_to_db': True
  }) 
}}

-- CTE for grabbing the onchain transaction data we care about, 
-- including project-collection mapping
WITH txns AS (
  SELECT
    pbc.collection_id,
    c.to_namespace AS onchain_network,
    a.project_id,
    c.from_source_id AS from_id,
    c.l2_gas,
    c.tx_count,
    DATE(TIMESTAMP_TRUNC(c.time, MONTH)) AS bucket_month
  FROM {{ ref('stg_dune__contract_invocation') }} AS c
  INNER JOIN {{ ref('stg_ossd__artifacts_by_project') }} AS a
    ON c.to_source_id = a.artifact_source_id
  INNER JOIN {{ ref('stg_ossd__projects_by_collection') }} AS pbc
    ON a.project_id = pbc.project_id
),

-- CTEs for calculating all-time and 6-month collection metrics across all
-- contracts
metrics_all_time AS (
  SELECT
    collection_id,
    onchain_network,
    COUNT(DISTINCT project_id) AS total_projects,
    MIN(bucket_month) AS first_txn_date,
    COUNT(DISTINCT from_id) AS total_users,
    SUM(l2_gas) AS total_l2_gas,
    SUM(tx_count) AS total_txns
  FROM txns
  GROUP BY collection_id, onchain_network
),

metrics_6_months AS (
  SELECT
    collection_id,
    onchain_network,
    COUNT(DISTINCT from_id) AS users_6_months,
    SUM(l2_gas) AS l2_gas_6_months,
    SUM(tx_count) AS txns_6_months
  FROM txns
  WHERE bucket_month >= DATE_ADD(CURRENT_DATE(), INTERVAL -6 MONTH)
  GROUP BY collection_id, onchain_network
),

-- CTE for identifying new users to the collection in the last 3 months
new_users AS (
  SELECT
    collection_id,
    onchain_network,
    SUM(is_new_user) AS new_user_count
  FROM (
    SELECT
      collection_id,
      onchain_network,
      from_id,
      CASE
        WHEN MIN(bucket_month) >= DATE_ADD(CURRENT_DATE(), INTERVAL -3 MONTH)
          THEN 1
        ELSE 0
      END AS is_new_user
    FROM txns
    GROUP BY collection_id, onchain_network, from_id
  )
  GROUP BY collection_id, onchain_network
),

-- CTEs for segmenting different types of active users based on txn volume at 
-- collection level
user_txns_aggregated AS (
  SELECT
    collection_id,
    onchain_network,
    from_id,
    SUM(tx_count) AS total_tx_count
  FROM txns
  WHERE bucket_month >= DATE_ADD(CURRENT_DATE(), INTERVAL -3 MONTH)
  GROUP BY collection_id, onchain_network, from_id
),

multi_project_users AS (
  SELECT
    onchain_network,
    from_id,
    COUNT(DISTINCT project_id) AS projects_transacted_on
  FROM txns
  WHERE bucket_month >= DATE_ADD(CURRENT_DATE(), INTERVAL -3 MONTH)
  GROUP BY onchain_network, from_id
),

user_segments AS (
  SELECT
    collection_id,
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
      uta.collection_id,
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
  GROUP BY collection_id, onchain_network
),

-- CTE to count the number of contracts deployed by projects in a collection
contracts AS (
  SELECT
    pbc.collection_id,
    a.artifact_namespace AS onchain_network,
    COUNT(DISTINCT a.artifact_source_id) AS num_contracts
  FROM {{ ref('stg_ossd__artifacts_by_project') }} AS a
  INNER JOIN {{ ref('stg_ossd__projects_by_collection') }} AS pbc
    ON a.project_id = pbc.project_id
  GROUP BY pbc.collection_id, onchain_network
),

collection_by_network AS (
  SELECT
    c.collection_id,
    c.collection_slug,
    c.collection_name,
    ctx.onchain_network
  FROM {{ ref('collections_v1') }} AS c
  INNER JOIN contracts AS ctx
    ON c.collection_id = ctx.collection_id
)

-- Final query to join all the metrics together for collections
SELECT
  c.collection_id,
  c.collection_slug,
  c.collection_name,
  c.onchain_network AS `artifact_namespace`,
  ma.total_projects AS `total_project_count`,
  co.num_contracts AS `total_contract_count`,
  ma.first_txn_date AS `first_transaction_date`,
  ma.total_txns AS `total_transaction_count`,
  m6.txns_6_months AS `transaction_count_6_months`,
  ma.total_l2_gas,
  m6.l2_gas_6_months,
  ma.total_users AS `total_user_address_count`,
  m6.users_6_months AS `user_address_count_6_months`,
  nu.new_user_count AS `new_user_count_3_months`,
  us.high_frequency_users AS `high_frequency_address_count`,
  us.more_active_users AS `more_active_user_address_count`,
  us.less_active_users AS `less_active_user_address_count`,
  us.multi_project_users AS `multi_project_user_address_count`,
  (
    us.high_frequency_users + us.more_active_users + us.less_active_users
  ) AS `total_active_user_address_count`
FROM collection_by_network AS c
INNER JOIN metrics_all_time AS ma
  ON
    c.collection_id = ma.collection_id
    AND c.onchain_network = ma.onchain_network
INNER JOIN metrics_6_months AS m6
  ON
    c.collection_id = m6.collection_id
    AND c.onchain_network = m6.onchain_network
INNER JOIN new_users AS nu
  ON
    c.collection_id = nu.collection_id
    AND c.onchain_network = nu.onchain_network
INNER JOIN user_segments AS us
  ON
    c.collection_id = us.collection_id
    AND c.onchain_network = us.onchain_network
INNER JOIN contracts AS co
  ON
    c.collection_id = co.collection_id
    AND c.onchain_network = co.onchain_network
