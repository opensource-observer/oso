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


-- CTE for grabbing the onchain transaction data we care about, including project-collection mapping
WITH txns AS (
  SELECT 
    pbc.collection_id,
    a.project_id,
    c.from_source_id AS from_id,
    DATE(TIMESTAMP_TRUNC(c.time, MONTH)) AS bucket_month,
    l2_gas,
    tx_count
  FROM {{ ref('stg_dune__arbitrum_contract_invocation') }} AS c
  JOIN {{ ref('stg_ossd__artifacts_by_project') }} AS a ON c.to_source_id = a.artifact_source_id
  JOIN {{ ref('stg_ossd__projects_by_collection') }} AS pbc ON a.project_id = pbc.project_id
),

-- CTEs for calculating all-time and 6-month collection metrics across all contracts
metrics_all_time AS (
  SELECT 
    collection_id,
    COUNT(DISTINCT project_id) AS total_projects,
    MIN(bucket_month) AS first_txn_date,
    COUNT(DISTINCT from_id) AS total_users,
    SUM(l2_gas) AS total_l2_gas,
    SUM(tx_count) AS total_txns
  FROM txns
  GROUP BY collection_id
),
metrics_6_months AS (
  SELECT 
    collection_id,
    COUNT(DISTINCT from_id) AS users_6_months,
    SUM(l2_gas) AS l2_gas_6_months,
    SUM(tx_count) AS txns_6_months
  FROM txns
  WHERE bucket_month >= DATE_ADD(CURRENT_DATE(), INTERVAL -6 MONTH) 
  GROUP BY collection_id
),

-- CTE for identifying new users to the collection in the last 3 months
new_users AS (
  SELECT
    collection_id,
    SUM(is_new_user) AS new_user_count
  FROM (
    SELECT
      collection_id,
      from_id,
      CASE WHEN MIN(bucket_month) >= DATE_ADD(CURRENT_DATE(), INTERVAL -3 MONTH) THEN 1 ELSE 0 END AS is_new_user
    FROM txns
    GROUP BY collection_id, from_id
  )
  GROUP BY collection_id
),

-- CTEs for segmenting different types of active users based on txn volume at collection level
user_txns_aggregated AS (
  SELECT
    collection_id,
    from_id,
    SUM(tx_count) AS total_tx_count
  FROM txns
  WHERE bucket_month >= DATE_ADD(CURRENT_DATE(), INTERVAL -3 MONTH)
  GROUP BY collection_id, from_id
),
multi_project_users AS (
  SELECT
    from_id,
    COUNT(DISTINCT project_id) AS projects_transacted_on
    FROM txns
    WHERE bucket_month >= DATE_ADD(CURRENT_DATE(), INTERVAL -3 MONTH)
    GROUP BY from_id
),
user_segments AS (
  SELECT
    collection_id,
    COUNT(DISTINCT CASE WHEN user_segment = 'HIGH_FREQUENCY_USER' THEN from_id END) AS high_frequency_users,
    COUNT(DISTINCT CASE WHEN user_segment = 'MORE_ACTIVE_USER' THEN from_id END) AS more_active_users,
    COUNT(DISTINCT CASE WHEN user_segment = 'LESS_ACTIVE_USER' THEN from_id END) AS less_active_users,
    COUNT(DISTINCT CASE WHEN projects_transacted_on >= 3 THEN from_id END) AS multi_project_users
  FROM (
    SELECT
      uta.collection_id,
      uta.from_id,
      CASE 
        WHEN uta.total_tx_count >= 1000 THEN 'HIGH_FREQUENCY_USER'
        WHEN uta.total_tx_count >= 10 THEN 'MORE_ACTIVE_USER'
        ELSE 'LESS_ACTIVE_USER'
      END AS user_segment,
        mpu.projects_transacted_on
    FROM user_txns_aggregated AS uta
    JOIN multi_project_users AS mpu ON uta.from_id = mpu.from_id
  )
  GROUP BY collection_id
),

-- CTE to count the number of contracts deployed by projects in a collection
contracts AS (
  SELECT
    pbc.collection_id,
    COUNT(DISTINCT a.artifact_source_id) AS num_contracts
  FROM {{ ref('stg_ossd__artifacts_by_project') }} AS a
  JOIN {{ ref('stg_ossd__projects_by_collection') }} AS pbc ON a.project_id = pbc.project_id
  GROUP BY pbc.collection_id
)

-- Final query to join all the metrics together for collections
SELECT
  c.collection_id,
  c.collection_name,
  co.num_contracts,
  ma.total_projects,
  ma.first_txn_date,
  ma.total_txns,
  ma.total_l2_gas,
  ma.total_users,
  m6.txns_6_months,
  m6.l2_gas_6_months,
  m6.users_6_months,  
  nu.new_user_count AS new_users,
  (us.high_frequency_users + us.more_active_users + us.less_active_users) AS active_users,
  us.high_frequency_users,
  us.more_active_users,
  us.less_active_users,
  us.multi_project_users
  
FROM {{ ref('collections') }} AS c
INNER JOIN metrics_all_time AS ma ON c.collection_id = ma.collection_id
INNER JOIN metrics_6_months AS m6 on c.collection_id = m6.collection_id
INNER JOIN new_users AS nu on c.collection_id = nu.collection_id
INNER JOIN user_segments AS us on c.collection_id = us.collection_id
INNER JOIN contracts AS co on c.collection_id = co.collection_id