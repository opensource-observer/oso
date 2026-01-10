MODEL (
  name oso.int_optimism_dex_user_ltv,
  description 'Lifetime value metrics for DEX users on OP Mainnet',
  dialect trino,
  kind full,
  audits (
    HAS_AT_LEAST_N_ROWS(threshold := 0)
  )
);


WITH dex_users AS (
  SELECT
    from_artifact_id,
    dex_address,
    project_name,
    MIN(bucket_day) AS date_first_transaction,
    SUM(count) AS total_transactions,
    SUM(l2_gas_fee) AS total_gas_fees
  FROM oso.int_optimism_dex_trades_daily
  GROUP BY 
    from_artifact_id,
    dex_address,
    project_name
),

user_activity AS (
  SELECT
    a.from_artifact_id,
    a.from_artifact_name,
    MIN(a.bucket_month) AS first_month_of_activity_on_op_mainnet,
    MAX(a.bucket_month) AS last_month_of_activity_on_op_mainnet,
    SUM(a.total_gas_fees) AS total_gas_fees_on_op_mainnet,
    SUM(a.total_transactions) AS total_transactions_on_op_mainnet
  FROM oso.int_optimism_user_activity_by_month AS a
  JOIN dex_users AS d
    ON a.from_artifact_id = d.from_artifact_id
  GROUP BY 1, 2
)

SELECT
  d.from_artifact_id,
  u.from_artifact_name AS user_address,
  d.dex_address,
  d.project_name,
  d.date_first_transaction,
  d.total_transactions,
  d.total_gas_fees,
  u.first_month_of_activity_on_op_mainnet,
  u.last_month_of_activity_on_op_mainnet,
  u.total_gas_fees_on_op_mainnet,
  u.total_transactions_on_op_mainnet
FROM dex_users AS d
JOIN user_activity AS u
  ON d.from_artifact_id = u.from_artifact_id