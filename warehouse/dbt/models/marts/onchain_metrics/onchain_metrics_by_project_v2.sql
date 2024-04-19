{{ 
  config(meta = {
    'sync_to_cloudsql': False
  }) 
}}

WITH txns AS (
  SELECT
    project_id,
    from_namespace AS network,
    MIN(bucket_day) AS first_txn_date,
    SUM(
      CASE
        WHEN event_type = 'CONTRACT_INVOCATION_DAILY_COUNT' THEN amount
      END
    ) AS total_txns,
    SUM(
      CASE
        WHEN event_type = 'CONTRACT_INVOCATION_DAILY_L2_GAS_USED' THEN amount
      END
    ) AS total_l2_gas,
    SUM(
      CASE
        WHEN
          event_type = 'CONTRACT_INVOCATION_DAILY_COUNT'
          AND DATE(bucket_day) >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH)
          THEN amount
      END
    ) AS txns_6_months,
    SUM(
      CASE
        WHEN
          event_type = 'CONTRACT_INVOCATION_DAILY_L2_GAS_USED'
          AND DATE(bucket_day) >= DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH)
          THEN amount
      END
    ) AS l2_gas_6_months
  FROM
    {{ ref('events_daily_to_project_by_source') }}
  WHERE
    event_type IN (
      'CONTRACT_INVOCATION_DAILY_L2_GAS_USED',
      'CONTRACT_INVOCATION_DAILY_COUNT'
    )
  GROUP BY
    1, 2
),

contracts AS (
  SELECT
    project_id,
    artifact_namespace AS network,
    COUNT(DISTINCT artifact_name) AS num_contracts
  FROM
    {{ ref('artifacts_by_project') }}
  WHERE
    artifact_type IN ('CONTRACT', 'FACTORY')
  GROUP BY
    1, 2
),

users AS (
  SELECT
    project_id,
    network,
    COUNT(DISTINCT from_id) AS total_addresses,
    COUNT(
      DISTINCT CASE
        WHEN rfm_recency >= 2 THEN from_id
      END
    ) AS addresses_6_months,
    COUNT(
      DISTINCT CASE
        WHEN rfm_frequency >= 4 THEN from_id
      END
    ) AS high_activity_addresses,
    COUNT(
      DISTINCT CASE
        WHEN rfm_frequency >= 2 AND rfm_frequency < 4 THEN from_id
      END
    ) AS med_activity_addresses,
    COUNT(
      DISTINCT CASE
        WHEN rfm_frequency < 2 THEN from_id
      END
    ) AS low_activity_addresses,
    COUNT(
      DISTINCT CASE
        WHEN rfm_ecosystem > 2 THEN from_id
      END
    ) AS multi_project_addresses
  FROM
    {{ ref('address_rfm_segments_by_project') }}
  GROUP BY
    1, 2
),

new_users AS (
  SELECT
    project_id,
    namespace AS network,
    COUNT(
      DISTINCT CASE
        WHEN user_status = 'new' THEN from_id
      END
    ) AS new_users,
    COUNT(DISTINCT from_id) AS active_users
  FROM
    {{ ref('new_users_monthly_to_project') }}
  GROUP BY
    1, 2
),

metrics AS (
  SELECT
    c.*,
    t.* EXCEPT (project_id, network),
    u.* EXCEPT (project_id, network),
    n.* EXCEPT (project_id, network)
  FROM
    contracts AS c
  INNER JOIN
    txns AS t
    ON c.project_id = t.project_id AND c.network = t.network
  LEFT JOIN
    users AS u
    ON t.project_id = u.project_id AND t.network = u.network
  LEFT JOIN
    new_users AS n
    ON t.project_id = n.project_id AND t.network = n.network
)

SELECT
  metrics.*,
  p.project_slug
FROM
  {{ ref('projects') }} AS p
LEFT JOIN
  metrics ON p.project_id = metrics.project_id
WHERE
  metrics.num_contracts IS NOT NULL
