MODEL (
  name oso.int_optimism_dex_user_cohorts,
  description 'DEX user cohorts on OP Mainnet',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  )
);

WITH user_first_day AS (
  SELECT
    from_artifact_id,
    MIN(date_first_transaction) AS first_day
  FROM oso.int_optimism_dex_user_ltv
  GROUP BY 1
),
user_first_dex AS (
  SELECT
    a.from_artifact_id,
    a.dex_address AS cohort_dex,
    a.first_day AS cohort_start_day,
    ROW_NUMBER() OVER (
      PARTITION BY a.from_artifact_id
      ORDER BY a.tx_count DESC, a.l2_gas_fee DESC, a.dex_address
    ) AS rn
  FROM (
    SELECT
      f.from_artifact_id,
      t.dex_address,
      f.first_day,
      SUM(t.count) AS tx_count,
      SUM(t.l2_gas_fee) AS l2_gas_fee
    FROM user_first_day AS f
    JOIN oso.int_optimism_dex_trades_daily AS t
      ON t.from_artifact_id = f.from_artifact_id
     AND t.bucket_day = f.first_day
    GROUP BY 1,2,3
  ) AS a
),
cohort_users AS (
  SELECT
    from_artifact_id,
    cohort_dex,
    cohort_start_day
  FROM user_first_dex
  WHERE rn = 1
),
user_dex_first_day AS (
  SELECT
    from_artifact_id,
    dex_address,
    date_first_transaction AS first_day_with_dex
  FROM oso.int_optimism_dex_user_ltv
),
user_day_dex AS (
  SELECT
    bucket_day,
    project_name,
    dex_address,
    from_artifact_id,
    SUM(count) AS tx_count,
    SUM(l2_gas_fee) AS tx_fees_eth
  FROM oso.int_optimism_dex_trades_daily
  GROUP BY 1,2,3,4
),
classified AS (
  SELECT
    u.bucket_day,
    u.project_name,
    u.dex_address,
    u.from_artifact_id,
    u.tx_count,
    u.tx_fees_eth,
    uf.first_day AS first_day_global,
    cu.cohort_dex,
    cu.cohort_start_day,
    udf.first_day_with_dex,
    CASE
      WHEN uf.first_day = u.bucket_day
       AND cu.cohort_dex = u.dex_address
        THEN 'new_onboarded_this_dex'
      WHEN udf.first_day_with_dex = u.bucket_day
       AND uf.first_day < u.bucket_day
       AND cu.cohort_dex <> u.dex_address
        THEN 'new_onboarded_other_dex'
      WHEN udf.first_day_with_dex < u.bucket_day
       AND cu.cohort_dex = u.dex_address
        THEN 'returning_onboarded_this_dex'
      WHEN udf.first_day_with_dex < u.bucket_day
       AND cu.cohort_dex <> u.dex_address
        THEN 'returning_onboarded_other_dex'
      ELSE 'other'
    END AS cohort_type
  FROM user_day_dex AS u
  LEFT JOIN user_first_day AS uf
    ON u.from_artifact_id = uf.from_artifact_id
  LEFT JOIN cohort_users AS cu
    ON u.from_artifact_id = cu.from_artifact_id
  LEFT JOIN user_dex_first_day AS udf
    ON u.from_artifact_id = udf.from_artifact_id
   AND u.dex_address = udf.dex_address
),
agg AS (
  SELECT
    bucket_day,
    project_name,
    dex_address,
    cohort_type,
    COUNT(DISTINCT from_artifact_id) AS address_count,
    SUM(tx_fees_eth) AS tx_fees_eth,
    SUM(tx_count) AS tx_count
  FROM classified
  WHERE cohort_type <> 'other'
  GROUP BY 1,2,3,4
),
all_days_projects AS (
  SELECT DISTINCT bucket_day, project_name, dex_address
  FROM oso.int_optimism_dex_trades_daily
),
cohort_types AS (
  SELECT 'new_onboarded_this_dex' AS cohort_type UNION ALL
  SELECT 'new_onboarded_other_dex' UNION ALL
  SELECT 'returning_onboarded_this_dex' UNION ALL
  SELECT 'returning_onboarded_other_dex'
),
grid AS (
  SELECT
    d.bucket_day,
    d.project_name,
    d.dex_address,
    c.cohort_type
  FROM all_days_projects AS d
  CROSS JOIN cohort_types AS c
)

SELECT
  g.bucket_day,
  g.project_name,
  g.dex_address,
  g.cohort_type,
  COALESCE(a.address_count,0) AS address_count,
  COALESCE(a.tx_fees_eth,0) AS tx_fees_eth,
  COALESCE(a.tx_count,0) AS tx_count
FROM grid AS g
LEFT JOIN agg AS a
  ON g.bucket_day = a.bucket_day
 AND g.project_name = a.project_name
 AND g.dex_address = a.dex_address
 AND g.cohort_type = a.cohort_type
ORDER BY
  bucket_day,
  project_name,
  dex_address,
  cohort_type