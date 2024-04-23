{{ 
  config(meta = {
    'sync_to_cloudsql': False
  }) 
}}

WITH txns AS (
  SELECT
    project_id,
    namespace AS network,
    SUM(CASE
      WHEN
        impact_metric = 'CONTRACT_INVOCATION_DAILY_COUNT_TOTAL'
        AND time_interval = 'ALL'
        THEN amount
    END) AS total_txns,
    SUM(CASE
      WHEN
        impact_metric = 'CONTRACT_INVOCATION_DAILY_L2_GAS_USED_TOTAL'
        AND time_interval = 'ALL'
        THEN amount
    END) AS total_l2_gas,
    SUM(CASE
      WHEN
        impact_metric = 'CONTRACT_INVOCATION_DAILY_COUNT_TOTAL'
        AND time_interval = '6M'
        THEN amount
    END) AS txns_6_months,
    SUM(CASE
      WHEN
        impact_metric = 'CONTRACT_INVOCATION_DAILY_L2_GAS_USED_TOTAL'
        AND time_interval = '6M'
        THEN amount
    END) AS l2_gas_6_months
  FROM {{ ref('event_totals_by_project') }}
  GROUP BY 1, 2
),

addresses AS (
  SELECT
    project_id,
    network,
    SUM(CASE
      WHEN
        impact_metric = 'NEW_ADDRESSES'
        AND time_interval = 'ALL'
        THEN amount
    END) AS total_addresses,
    SUM(CASE
      WHEN
        impact_metric = 'NEW_ADDRESSES'
        AND time_interval = '90D'
        THEN amount
    END) AS new_addresses,
    SUM(CASE
      WHEN
        impact_metric = 'RETURNING_ADDRESSES'
        AND time_interval = '90D'
        THEN amount
    END) AS returning_addresses,
    SUM(CASE
      WHEN
        impact_metric = 'LOW_ACTIVITY_ADDRESSES'
        AND time_interval = '90D'
        THEN amount
    END) AS low_activity_addresses,
    SUM(CASE
      WHEN
        impact_metric = 'MEDIUM_ACTIVITY_ADDRESSES'
        AND time_interval = '90D'
        THEN amount
    END) AS med_activity_addresses,
    SUM(CASE
      WHEN
        impact_metric = 'HIGH_ACTIVITY_ADDRESSES'
        AND time_interval = '90D'
        THEN amount
    END) AS high_activity_addresses
  FROM {{ ref('address_totals_by_project') }}
  GROUP BY 1, 2
),

first_txn AS (
  SELECT
    project_id,
    from_namespace AS network,
    MIN(bucket_day) AS date_first_txn
  FROM {{ ref('int_addresses_daily_activity') }}
  GROUP BY 1, 2
),

contracts AS (
  SELECT
    project_id,
    artifact_namespace AS network,
    COUNT(DISTINCT artifact_name) AS num_contracts
  FROM {{ ref('artifacts_by_project') }}
  WHERE artifact_type IN ('CONTRACT', 'FACTORY')
  GROUP BY 1, 2
),

multi_project_addresses AS (
  SELECT
    project_id,
    network,
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

metrics AS (
  SELECT
    c.*,
    f.* EXCEPT (project_id, network),
    t.* EXCEPT (project_id, network),
    a.* EXCEPT (project_id, network),
    m.* EXCEPT (project_id, network)
  FROM
    contracts AS c
  INNER JOIN
    txns AS t
    ON c.project_id = t.project_id AND c.network = t.network
  LEFT JOIN
    first_txn AS f
    ON t.project_id = f.project_id AND t.network = f.network
  LEFT JOIN
    addresses AS a
    ON t.project_id = a.project_id AND t.network = a.network
  LEFT JOIN
    multi_project_addresses AS m
    ON t.project_id = m.project_id AND t.network = m.network
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
