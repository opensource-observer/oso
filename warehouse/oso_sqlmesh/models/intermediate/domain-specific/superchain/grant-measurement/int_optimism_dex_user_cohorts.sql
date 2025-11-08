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
    MIN(bucket_day) AS first_day
  FROM oso.int_optimism_dex_trades
  GROUP BY 1
),
user_first_dex AS (
  SELECT
    a.from_artifact_id,
    a.dex_address,
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
    JOIN oso.int_optimism_dex_trades t
      ON t.from_artifact_id = f.from_artifact_id
     AND t.bucket_day = f.first_day
    GROUP BY 1,2,3
  ) AS a
),
cohort_users AS (
  SELECT
    from_artifact_id,
    dex_address,
    cohort_start_day
  FROM user_first_dex
  WHERE rn = 1
),
daily_new AS (
  SELECT
    t.bucket_day,
    t.project_name,
    t.dex_address,
    COUNT(DISTINCT t.from_artifact_id) AS new_address_count,
    SUM(t.l2_gas_fee) AS new_fees_eth
  FROM oso.int_optimism_dex_trades AS t
  JOIN cohort_users AS u
    ON t.from_artifact_id = u.from_artifact_id
   AND t.bucket_day >= u.cohort_start_day
  GROUP BY 1,2,3
),
daily_all AS (
  SELECT
    bucket_day,
    project_name,
    dex_address,
    COUNT(DISTINCT from_artifact_id) AS all_address_count,
    SUM(l2_gas_fee) AS all_fees_eth
  FROM oso.int_optimism_dex_trades
  GROUP BY 1,2,3
),
all_days_projects AS (
  SELECT
    bucket_day,
    project_name,
    dex_address
  FROM daily_all
  UNION
  SELECT
    bucket_day,
    project_name,
    dex_address
  FROM daily_new
),
joined AS (
  SELECT
    a.bucket_day,
    a.project_name,
    a.dex_address,
    COALESCE(all_address_count,0) AS all_addr,
    COALESCE(new_address_count,0) AS new_addr,
    COALESCE(all_fees_eth,0) AS all_fees_eth,
    COALESCE(new_fees_eth,0) AS new_fees_eth
  FROM all_days_projects AS a
  LEFT JOIN daily_all AS al
    ON a.bucket_day = al.bucket_day
   AND a.dex_address = al.dex_address
  LEFT JOIN daily_new AS nw
    ON a.bucket_day = nw.bucket_day
   AND a.dex_address = nw.dex_address
)
SELECT
  bucket_day,
  project_name,
  dex_address,
  new_addr AS address_count,
  new_fees_eth AS tx_fees_eth,
  'new addresses' AS cohort
FROM joined

UNION ALL

SELECT
  bucket_day,
  project_name,
  dex_address,
  all_addr,
  all_fees_eth,
  'all addresses' AS cohort
FROM joined

UNION ALL

SELECT
  bucket_day,
  project_name,
  dex_address,
  (all_addr - new_addr) AS address_count,
  (all_fees_eth - new_fees_eth) AS tx_fees_eth,
  'existing addresses' AS cohort
FROM joined
ORDER BY
  project_name,
  bucket_day,
  cohort