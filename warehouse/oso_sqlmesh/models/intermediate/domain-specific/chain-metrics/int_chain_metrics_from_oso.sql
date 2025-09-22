MODEL (
  name oso.int_chain_metrics_from_oso,
  description "Chain-level metrics from OSO",
  kind FULL,
  dialect trino,
  grain (sample_date, chain, metric_name),
  audits (
    has_at_least_n_rows(threshold := 0),
  ),
);

WITH contract_metrics AS (
  SELECT
    sample_date,
    chain,
    metric_name,
    amount
  FROM oso.int_chain_metrics_from_oso_contracts
),

l2_transactions_metrics AS (
  SELECT
    sample_date,
    chain,
    metric_name,
    amount
  FROM oso.int_chain_metrics_from_oso_l2_transactions
),

l2_4337_userops_metrics AS (
  SELECT
    sample_date,
    chain,
    metric_name,
    amount
  FROM oso.int_chain_metrics_from_oso_4337_userops
),

union_metrics AS (
  SELECT * FROM contract_metrics
  UNION ALL
  SELECT * FROM l2_transactions_metrics
  UNION ALL
  SELECT * FROM l2_4337_userops_metrics
)

SELECT
  sample_date,
  chain,
  metric_name,
  amount
FROM union_metrics