MODEL(
  name oso.int_chain_metrics,
  description 'Chain metrics',
  dialect trino,
  kind full,
  partitioned_by (DAY("sample_date"), "chain", "metric_name"),
  audits (
    has_at_least_n_rows(threshold := 0)
  )
);

WITH gtp_metrics AS (
  SELECT
    sample_date,
    'GROWTHEPIE' AS source,
    chain,
    metric_name,
    amount
  FROM oso.int_chain_metrics_from_growthepie
),

defillama_metrics AS (
  SELECT
    sample_date,
    'DEFILLAMA' AS source,
    chain,
    metric_name,
    amount
  FROM oso.int_chain_metrics_from_defillama
),

l2beat_metrics AS (
  SELECT
    sample_date,
    'L2BEAT' AS source,
    chain,
    metric_name,
    amount
  FROM oso.int_chain_metrics_from_l2beat
),

oso_metrics AS (
  SELECT
    sample_date,
    'OSO' AS source,
    chain,
    metric_name,
    amount
  FROM oso.int_chain_metrics_from_oso
),

union_metrics AS (
  SELECT * FROM gtp_metrics
  UNION ALL
  SELECT * FROM defillama_metrics
  UNION ALL
  SELECT * FROM l2beat_metrics
  UNION ALL
  SELECT * FROM oso_metrics
)

SELECT
  sample_date,
  source,
  chain,
  metric_name,
  amount
FROM union_metrics